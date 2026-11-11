from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_db
from app.models.negotiation_offer import NegotiationOffer
from app.models.payment_attempt import PaymentAttempt
from app.models.purchase_request import PurchaseRequest
from app.schemas.payments import PaymentCreate, PaymentRead
from app.services.audit import record_audit_event
from app.services.buyer_authorization import verify_buyer_token
from app.services.paypal import PayPalError, PayPalGateway

router = APIRouter(prefix="/purchase-requests", tags=["payments"])
DatabaseSession = Annotated[AsyncSession, Depends(get_db)]


async def _locked_request(db: AsyncSession, request_id: UUID) -> PurchaseRequest:
    result = await db.execute(
        select(PurchaseRequest).where(PurchaseRequest.id == request_id).with_for_update()
    )
    request = result.scalar_one_or_none()
    if request is None:
        raise HTTPException(status_code=404, detail="Purchase request not found")
    return request


@router.post("/{request_id}/payments", response_model=PaymentRead, status_code=201)
async def create_payment(
    request_id: UUID,
    payload: PaymentCreate,
    db: DatabaseSession,
    buyer_authorization: Annotated[str | None, Header(alias="X-Buyer-Authorization")] = None,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> PaymentAttempt:
    if not idempotency_key or not idempotency_key.strip() or len(idempotency_key) > 128:
        raise HTTPException(status_code=400, detail="A valid Idempotency-Key header is required")
    idempotency_key = idempotency_key.strip()

    request = await _locked_request(db, request_id)
    if not verify_buyer_token(request, buyer_authorization):
        raise HTTPException(status_code=401, detail="Valid buyer authorization is required")
    if request.version != payload.expected_request_version:
        raise HTTPException(status_code=409, detail="Purchase request changed; refresh before payment")

    existing = await db.scalar(
        select(PaymentAttempt).where(PaymentAttempt.idempotency_key == idempotency_key)
    )
    if existing is not None:
        if existing.purchase_request_id != request_id:
            raise HTTPException(status_code=409, detail="Idempotency key was used for another request")
        return existing
    if request.status != "accepted":
        raise HTTPException(status_code=409, detail="Only an accepted purchase request can be paid")

    offer = await db.scalar(
        select(NegotiationOffer).where(
            NegotiationOffer.purchase_request_id == request_id,
            NegotiationOffer.status == "accepted",
        )
    )
    if offer is None:
        raise HTTPException(status_code=409, detail="Accepted offer not found")
    if offer.currency != request.currency and request.currency:
        raise HTTPException(status_code=409, detail="Accepted offer currency does not match request")

    try:
        result = await PayPalGateway(get_settings()).create_order(
            request_id=str(request.id),
            offer_id=str(offer.id),
            amount=offer.amount,
            currency=offer.currency,
            idempotency_key=idempotency_key,
        )
    except PayPalError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    attempt = PaymentAttempt(
        purchase_request_id=request_id,
        accepted_offer_id=offer.id,
        paypal_order_id=result["order_id"],
        idempotency_key=idempotency_key,
        amount=offer.amount,
        currency=offer.currency,
        status="created",
        approval_url=result["approval_url"],
    )
    db.add(attempt)
    await db.flush()
    record_audit_event(
        db,
        purchase_request_id=request.id,
        actor_role="buyer",
        actor_authenticated=True,
        action="payment.order_created",
        entity_type="payment_attempt",
        entity_id=str(attempt.id),
        request_version=request.version,
        details={"amount": str(attempt.amount), "currency": attempt.currency, "status": attempt.status},
    )
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        duplicate = await db.scalar(
            select(PaymentAttempt).where(PaymentAttempt.idempotency_key == idempotency_key)
        )
        if duplicate is not None:
            return duplicate
        raise HTTPException(status_code=409, detail="Payment attempt conflicted with another request") from exc
    await db.refresh(attempt)
    return attempt


@router.post("/{request_id}/payments/{payment_id}/capture", response_model=PaymentRead)
async def capture_payment(
    request_id: UUID,
    payment_id: UUID,
    payload: PaymentCreate,
    db: DatabaseSession,
    buyer_authorization: Annotated[str | None, Header(alias="X-Buyer-Authorization")] = None,
) -> PaymentAttempt:
    request = await _locked_request(db, request_id)
    if not verify_buyer_token(request, buyer_authorization):
        raise HTTPException(status_code=401, detail="Valid buyer authorization is required")
    if request.version != payload.expected_request_version:
        raise HTTPException(status_code=409, detail="Purchase request changed; refresh before capture")
    attempt = await db.scalar(
        select(PaymentAttempt)
        .where(
            PaymentAttempt.id == payment_id,
            PaymentAttempt.purchase_request_id == request_id,
        )
        .with_for_update()
    )
    if attempt is None:
        raise HTTPException(status_code=404, detail="Payment attempt not found")
    if attempt.status == "captured":
        return attempt
    if attempt.status != "created":
        raise HTTPException(status_code=409, detail="Payment attempt is not capturable")

    try:
        result = await PayPalGateway(get_settings()).capture_order(
            attempt.paypal_order_id,
            f"{attempt.idempotency_key}-capture",
        )
    except PayPalError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    attempt.status = "captured"
    attempt.paypal_capture_id = result["capture_id"]
    attempt.captured_at = datetime.now(UTC)
    record_audit_event(
        db,
        purchase_request_id=request.id,
        actor_role="buyer",
        actor_authenticated=True,
        action="payment.captured",
        entity_type="payment_attempt",
        entity_id=str(attempt.id),
        request_version=request.version,
        details={"capture_id": attempt.paypal_capture_id, "status": attempt.status},
    )
    await db.commit()
    await db.refresh(attempt)
    return attempt
