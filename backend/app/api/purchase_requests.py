from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.purchase_request import PurchaseRequest
from app.schemas.purchase_request import (
    ConfirmPurchaseRequest,
    PurchaseIntentInput,
    PurchaseIntentPreview,
    PurchaseRequestCreated,
    PurchaseRequestRead,
)
from app.services.buyer_authorization import issue_buyer_token, verify_buyer_token
from app.services.purchase_intent import extract_purchase_intent

router = APIRouter(prefix="/purchase-requests", tags=["purchase requests"])
DatabaseSession = Annotated[AsyncSession, Depends(get_db)]


@router.post("/preview", response_model=PurchaseIntentPreview)
async def preview_purchase_intent(payload: PurchaseIntentInput) -> PurchaseIntentPreview:
    return extract_purchase_intent(payload.text)


@router.post("", response_model=PurchaseRequestCreated, status_code=status.HTTP_201_CREATED)
async def create_purchase_request(
    payload: PurchaseIntentInput,
    db: DatabaseSession,
) -> PurchaseRequestCreated:
    intent = extract_purchase_intent(payload.text)
    buyer_token, token_hash = issue_buyer_token()
    request = PurchaseRequest(
        raw_text=payload.text,
        item_description=intent.item_description,
        quantity=intent.quantity,
        unit=intent.unit,
        budget_amount=intent.budget_amount,
        currency=intent.currency,
        delivery_location=intent.delivery_location,
        required_by=intent.required_by,
        missing_fields=intent.missing_fields,
        buyer_token_hash=token_hash,
        status="draft",
        version=1,
    )
    db.add(request)
    await db.commit()
    await db.refresh(request)
    return PurchaseRequestCreated.model_validate(request).model_copy(
        update={"buyer_access_token": buyer_token}
    )


@router.get("/{request_id}", response_model=PurchaseRequestRead)
async def get_purchase_request(request_id: UUID, db: DatabaseSession) -> PurchaseRequest:
    request = await db.get(PurchaseRequest, request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="Purchase request not found")
    return request


@router.post("/{request_id}/confirm", response_model=PurchaseRequestRead)
async def confirm_purchase_request(
    request_id: UUID,
    payload: ConfirmPurchaseRequest,
    db: DatabaseSession,
    buyer_authorization: Annotated[str | None, Header(alias="X-Buyer-Authorization")] = None,
) -> PurchaseRequest:
    result = await db.execute(
        select(PurchaseRequest).where(PurchaseRequest.id == request_id).with_for_update()
    )
    request = result.scalar_one_or_none()
    if request is None:
        raise HTTPException(status_code=404, detail="Purchase request not found")
    if not verify_buyer_token(request, buyer_authorization):
        raise HTTPException(status_code=401, detail="Valid buyer authorization is required")
    if request.version != payload.expected_version:
        raise HTTPException(status_code=409, detail="Purchase request changed; review it again")
    if not payload.confirm:
        raise HTTPException(status_code=400, detail="Explicit confirmation is required")
    if request.status != "draft":
        raise HTTPException(status_code=409, detail="Only draft requests can be confirmed")
    if request.missing_fields:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Complete required fields before confirmation",
                "missing_fields": request.missing_fields,
            },
        )
    request.status = "confirmed"
    request.version += 1
    request.confirmed_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(request)
    return request
