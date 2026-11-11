from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.negotiation_offer import NegotiationOffer
from app.models.purchase_request import PurchaseRequest
from app.schemas.negotiation import (
    NegotiationOfferCreate,
    NegotiationOfferRead,
    NegotiationResponse,
)
from app.services.integrity import evaluate_purchase_integrity
from app.services.negotiation import (
    NegotiationState,
    validate_new_offer,
    validate_response,
)

router = APIRouter(prefix="/purchase-requests", tags=["negotiations"])
DatabaseSession = Annotated[AsyncSession, Depends(get_db)]


async def _locked_request(db: AsyncSession, request_id: UUID) -> PurchaseRequest:
    result = await db.execute(
        select(PurchaseRequest).where(PurchaseRequest.id == request_id).with_for_update()
    )
    request = result.scalar_one_or_none()
    if request is None:
        raise HTTPException(status_code=404, detail="Purchase request not found")
    return request


async def _request_offers(db: AsyncSession, request_id: UUID) -> list[NegotiationOffer]:
    result = await db.execute(
        select(NegotiationOffer).where(NegotiationOffer.purchase_request_id == request_id)
    )
    return list(result.scalars().all())


def _check_version(request: PurchaseRequest, expected_version: int) -> None:
    if request.version != expected_version:
        raise HTTPException(status_code=409, detail="Purchase request changed; refresh before continuing")


def _raise_integrity_conflict(issues: list[dict[str, str]]) -> None:
    raise HTTPException(
        status_code=409,
        detail={"message": "The operation would violate purchase integrity rules", "issues": issues},
    )


@router.get("/{request_id}/offers", response_model=list[NegotiationOfferRead])
async def list_offers(request_id: UUID, db: DatabaseSession) -> list[NegotiationOffer]:
    request = await db.get(PurchaseRequest, request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="Purchase request not found")
    result = await db.execute(
        select(NegotiationOffer)
        .where(NegotiationOffer.purchase_request_id == request_id)
        .order_by(NegotiationOffer.created_at, NegotiationOffer.id)
    )
    return list(result.scalars().all())


@router.post(
    "/{request_id}/offers",
    response_model=NegotiationOfferRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_offer(
    request_id: UUID,
    payload: NegotiationOfferCreate,
    db: DatabaseSession,
) -> NegotiationOffer:
    request = await _locked_request(db, request_id)
    _check_version(request, payload.expected_request_version)
    offers = await _request_offers(db, request_id)

    parent: NegotiationOffer | None = None
    if payload.in_reply_to_offer_id is not None:
        parent = next(
            (offer for offer in offers if offer.id == payload.in_reply_to_offer_id),
            None,
        )
        if parent is None:
            raise HTTPException(status_code=404, detail="Offer to counter was not found")
        if parent.status != "open":
            raise HTTPException(status_code=409, detail="Only an open offer can be countered")
    elif any(offer.status == "open" for offer in offers):
        raise HTTPException(status_code=409, detail="An open offer must be countered or resolved first")

    if offers and payload.currency != offers[0].currency:
        raise HTTPException(status_code=409, detail="Offer currency must remain consistent")
    if request.currency and payload.currency != request.currency:
        raise HTTPException(status_code=409, detail="Offer currency must match the purchase budget currency")

    try:
        validate_new_offer(
            NegotiationState(request.status, request.version),
            payload.actor_role,
            payload.amount,
            parent.proposer_role if parent else None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    if parent is not None:
        parent.status = "superseded"
        parent.responded_at = datetime.now(UTC)

    offer = NegotiationOffer(
        purchase_request_id=request_id,
        proposer_role=payload.actor_role,
        amount=payload.amount,
        currency=payload.currency,
        message=payload.message,
        in_reply_to_offer_id=payload.in_reply_to_offer_id,
        status="open",
    )
    request.status = "negotiating"
    request.version += 1
    report = evaluate_purchase_integrity(request, [*offers, offer])
    if not report.is_valid:
        await db.rollback()
        _raise_integrity_conflict(
            [{"code": issue.code, "message": issue.message} for issue in report.issues]
        )

    db.add(offer)
    await db.commit()
    await db.refresh(offer)
    return offer


async def _respond_to_offer(
    request_id: UUID,
    offer_id: UUID,
    payload: NegotiationResponse,
    db: AsyncSession,
    decision: str,
) -> NegotiationOffer:
    request = await _locked_request(db, request_id)
    _check_version(request, payload.expected_request_version)
    offers = await _request_offers(db, request_id)
    offer = next((item for item in offers if item.id == offer_id), None)
    if offer is None:
        raise HTTPException(status_code=404, detail="Offer not found")

    try:
        validate_response(
            NegotiationState(request.status, request.version),
            offer.status,
            offer.proposer_role,
            payload.actor_role,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    offer.status = decision
    offer.responded_at = datetime.now(UTC)
    if decision == "accepted":
        request.status = "accepted"
        for competing_offer in offers:
            if competing_offer.id != offer.id and competing_offer.status == "open":
                competing_offer.status = "superseded"
                competing_offer.responded_at = datetime.now(UTC)
    request.version += 1

    report = evaluate_purchase_integrity(request, offers)
    if not report.is_valid:
        await db.rollback()
        _raise_integrity_conflict(
            [{"code": issue.code, "message": issue.message} for issue in report.issues]
        )

    await db.commit()
    await db.refresh(offer)
    return offer


@router.post("/{request_id}/offers/{offer_id}/accept", response_model=NegotiationOfferRead)
async def accept_offer(
    request_id: UUID,
    offer_id: UUID,
    payload: NegotiationResponse,
    db: DatabaseSession,
) -> NegotiationOffer:
    return await _respond_to_offer(request_id, offer_id, payload, db, "accepted")


@router.post("/{request_id}/offers/{offer_id}/reject", response_model=NegotiationOfferRead)
async def reject_offer(
    request_id: UUID,
    offer_id: UUID,
    payload: NegotiationResponse,
    db: DatabaseSession,
) -> NegotiationOffer:
    return await _respond_to_offer(request_id, offer_id, payload, db, "rejected")
