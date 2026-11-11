from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.negotiation_offer import NegotiationOffer
from app.models.purchase_request import PurchaseRequest
from app.schemas.integrity import IntegrityReportRead
from app.services.buyer_authorization import verify_buyer_token
from app.services.integrity import evaluate_purchase_integrity

router = APIRouter(prefix="/purchase-requests", tags=["integrity"])
DatabaseSession = Annotated[AsyncSession, Depends(get_db)]


@router.get("/{request_id}/integrity", response_model=IntegrityReportRead)
async def get_purchase_integrity(
    request_id: UUID,
    db: DatabaseSession,
    buyer_authorization: Annotated[str | None, Header(alias="X-Buyer-Authorization")] = None,
) -> IntegrityReportRead:
    request = await db.get(PurchaseRequest, request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="Purchase request not found")
    if not verify_buyer_token(request, buyer_authorization):
        raise HTTPException(status_code=401, detail="Valid buyer authorization is required")

    result = await db.execute(
        select(NegotiationOffer)
        .where(NegotiationOffer.purchase_request_id == request_id)
        .order_by(NegotiationOffer.created_at, NegotiationOffer.id)
    )
    report = evaluate_purchase_integrity(request, list(result.scalars().all()))
    return IntegrityReportRead(
        purchase_request_id=report.purchase_request_id,
        request_status=report.request_status,
        request_version=report.request_version,
        is_valid=report.is_valid,
        issues=[{"code": issue.code, "message": issue.message} for issue in report.issues],
    )
