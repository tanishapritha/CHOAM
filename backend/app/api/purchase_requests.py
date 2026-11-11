from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.audit_event import AuditEvent
from app.models.purchase_request import PurchaseRequest
from app.schemas.audit import AuditEventRead
from app.schemas.purchase_request import (
    ConfirmPurchaseRequest,
    PurchaseIntentInput,
    PurchaseIntentPreview,
    PurchaseRequestCreated,
    PurchaseRequestRead,
)
from app.services.audit import record_audit_event
from app.services.buyer_authorization import issue_buyer_token, verify_buyer_token
from app.services.purchase_intent import extract_purchase_intent

router = APIRouter(prefix="/purchase-requests", tags=["purchase requests"])
DatabaseSession = Annotated[AsyncSession, Depends(get_db)]


def _require_buyer(request: PurchaseRequest, token: str | None) -> None:
    if not verify_buyer_token(request, token):
        raise HTTPException(status_code=401, detail="Valid buyer authorization is required")


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
    await db.flush()
    record_audit_event(
        db,
        purchase_request_id=request.id,
        actor_role="buyer",
        actor_authenticated=True,
        action="purchase_request.created",
        entity_type="purchase_request",
        entity_id=str(request.id),
        request_version=request.version,
        details={"status": request.status},
    )
    await db.commit()
    await db.refresh(request)
    return PurchaseRequestCreated.model_validate(request).model_copy(
        update={"buyer_access_token": buyer_token}
    )


@router.get("/{request_id}", response_model=PurchaseRequestRead)
async def get_purchase_request(
    request_id: UUID,
    db: DatabaseSession,
    buyer_authorization: Annotated[str | None, Header(alias="X-Buyer-Authorization")] = None,
) -> PurchaseRequest:
    request = await db.get(PurchaseRequest, request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="Purchase request not found")
    _require_buyer(request, buyer_authorization)
    return request


@router.get("/{request_id}/audit", response_model=list[AuditEventRead])
async def list_audit_events(
    request_id: UUID,
    db: DatabaseSession,
    buyer_authorization: Annotated[str | None, Header(alias="X-Buyer-Authorization")] = None,
) -> list[AuditEvent]:
    request = await db.get(PurchaseRequest, request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="Purchase request not found")
    _require_buyer(request, buyer_authorization)
    result = await db.execute(
        select(AuditEvent)
        .where(AuditEvent.purchase_request_id == request_id)
        .order_by(AuditEvent.created_at, AuditEvent.id)
    )
    return list(result.scalars().all())


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
    _require_buyer(request, buyer_authorization)
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
    record_audit_event(
        db,
        purchase_request_id=request.id,
        actor_role="buyer",
        actor_authenticated=True,
        action="purchase_request.confirmed",
        entity_type="purchase_request",
        entity_id=str(request.id),
        request_version=request.version,
        details={"status": request.status},
    )
    await db.commit()
    await db.refresh(request)
    return request
