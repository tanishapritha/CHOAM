from uuid import UUID

from mcp.server.fastmcp import FastMCP
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.negotiation_offer import NegotiationOffer
from app.models.purchase_request import PurchaseRequest
from app.services.buyer_authorization import verify_buyer_token
from app.services.integrity import evaluate_purchase_integrity
from app.services.purchase_intent import extract_purchase_intent

mcp = FastMCP("CHOAM commerce")


@mcp.tool()
def preview_purchase_intent(text: str) -> dict:
    """Parse a buyer's purchase text into explicit fields without creating a request."""
    return extract_purchase_intent(text).model_dump(mode="json")


@mcp.tool()
async def get_purchase_request(request_id: str, buyer_access_token: str) -> dict:
    """Read a purchase request after validating its one-time buyer access token."""
    try:
        parsed_id = UUID(request_id)
    except ValueError:
        return {"error": "Invalid purchase request ID"}
    async with SessionLocal() as db:
        request = await db.get(PurchaseRequest, parsed_id)
        if request is None:
            return {"error": "Purchase request not found"}
        if not verify_buyer_token(request, buyer_access_token):
            return {"error": "Buyer authorization failed"}
        return {
            "id": str(request.id),
            "status": request.status,
            "version": request.version,
            "item_description": request.item_description,
            "quantity": request.quantity,
            "unit": request.unit,
            "budget_amount": str(request.budget_amount) if request.budget_amount is not None else None,
            "currency": request.currency,
            "delivery_location": request.delivery_location,
            "required_by": request.required_by,
            "missing_fields": request.missing_fields,
        }


@mcp.tool()
async def list_negotiation_offers(request_id: str, buyer_access_token: str) -> list[dict] | dict:
    """List offer history only after validating the buyer access token."""
    try:
        parsed_id = UUID(request_id)
    except ValueError:
        return {"error": "Invalid purchase request ID"}
    async with SessionLocal() as db:
        request = await db.get(PurchaseRequest, parsed_id)
        if request is None:
            return {"error": "Purchase request not found"}
        if not verify_buyer_token(request, buyer_access_token):
            return {"error": "Buyer authorization failed"}
        result = await db.execute(
            select(NegotiationOffer)
            .where(NegotiationOffer.purchase_request_id == parsed_id)
            .order_by(NegotiationOffer.created_at, NegotiationOffer.id)
        )
        return [
            {
                "id": str(offer.id),
                "proposer_role": offer.proposer_role,
                "amount": str(offer.amount),
                "currency": offer.currency,
                "message": offer.message,
                "status": offer.status,
                "in_reply_to_offer_id": str(offer.in_reply_to_offer_id) if offer.in_reply_to_offer_id else None,
            }
            for offer in result.scalars().all()
        ]


@mcp.tool()
async def check_purchase_integrity(request_id: str, buyer_access_token: str) -> dict:
    """Evaluate purchase and offer invariants for an authorized buyer."""
    try:
        parsed_id = UUID(request_id)
    except ValueError:
        return {"error": "Invalid purchase request ID"}
    async with SessionLocal() as db:
        request = await db.get(PurchaseRequest, parsed_id)
        if request is None:
            return {"error": "Purchase request not found"}
        if not verify_buyer_token(request, buyer_access_token):
            return {"error": "Buyer authorization failed"}
        result = await db.execute(
            select(NegotiationOffer).where(NegotiationOffer.purchase_request_id == parsed_id)
        )
        report = evaluate_purchase_integrity(request, list(result.scalars().all()))
        return {
            "purchase_request_id": str(report.purchase_request_id),
            "request_status": report.request_status,
            "request_version": report.request_version,
            "is_valid": report.is_valid,
            "issues": [{"code": issue.code, "message": issue.message} for issue in report.issues],
        }


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
