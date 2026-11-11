from dataclasses import dataclass
from decimal import Decimal
from typing import Sequence
from uuid import UUID

from app.models.negotiation_offer import NegotiationOffer
from app.models.purchase_request import PurchaseRequest


@dataclass(frozen=True)
class IntegrityIssue:
    code: str
    message: str


@dataclass(frozen=True)
class IntegrityReport:
    purchase_request_id: UUID
    request_status: str
    request_version: int
    is_valid: bool
    issues: tuple[IntegrityIssue, ...]


def evaluate_purchase_integrity(
    request: PurchaseRequest,
    offers: Sequence[NegotiationOffer],
) -> IntegrityReport:
    """Evaluate persisted purchase and negotiation state without side effects."""
    issues: list[IntegrityIssue] = []
    valid_request_statuses = {"draft", "confirmed", "negotiating", "accepted"}
    valid_offer_statuses = {"open", "accepted", "rejected", "superseded"}

    if request.status not in valid_request_statuses:
        issues.append(IntegrityIssue("unknown_request_status", "Purchase request status is not supported"))
    if request.version < 1:
        issues.append(IntegrityIssue("invalid_request_version", "Purchase request version must be positive"))
    if request.status != "draft" and request.missing_fields:
        issues.append(IntegrityIssue("incomplete_confirmed_request", "A non-draft request has missing required fields"))

    offer_by_id = {offer.id: offer for offer in offers}
    accepted_offers: list[NegotiationOffer] = []
    open_offers: list[NegotiationOffer] = []
    currencies: set[str] = set()

    for offer in offers:
        if offer.purchase_request_id != request.id:
            issues.append(IntegrityIssue("foreign_offer", "An offer belongs to a different purchase request"))
        if offer.proposer_role not in {"buyer", "seller"}:
            issues.append(IntegrityIssue("invalid_proposer_role", "Offer proposer must be buyer or seller"))
        if offer.status not in valid_offer_statuses:
            issues.append(IntegrityIssue("unknown_offer_status", "Offer status is not supported"))
        if offer.amount is None or offer.amount <= Decimal("0"):
            issues.append(IntegrityIssue("invalid_offer_amount", "Offer amount must be greater than zero"))
        if not isinstance(offer.currency, str) or len(offer.currency) != 3 or not offer.currency.isalpha() or offer.currency != offer.currency.upper():
            issues.append(IntegrityIssue("invalid_offer_currency", "Offer currency must be a three-letter uppercase code"))
        else:
            currencies.add(offer.currency)
        if request.currency and offer.currency != request.currency:
            issues.append(IntegrityIssue("currency_mismatch", "Offer currency must match the buyer budget currency"))
        if offer.status == "accepted":
            accepted_offers.append(offer)
        if offer.status == "open":
            open_offers.append(offer)

    if len(currencies) > 1:
        issues.append(IntegrityIssue("offer_currency_changed", "Currency must remain consistent throughout negotiation"))

    for offer in offers:
        if offer.in_reply_to_offer_id is None:
            continue
        parent = offer_by_id.get(offer.in_reply_to_offer_id)
        if parent is None:
            issues.append(IntegrityIssue("missing_counteroffer_parent", "Counteroffer parent must exist in this request"))
            continue
        if parent.purchase_request_id != request.id:
            issues.append(IntegrityIssue("foreign_counteroffer_parent", "Counteroffer parent belongs to another request"))
        if parent.proposer_role == offer.proposer_role:
            issues.append(IntegrityIssue("same_party_counteroffer", "Counteroffer must come from the other party"))
        if parent.status != "superseded":
            issues.append(IntegrityIssue("active_counteroffer_parent", "A countered offer must be marked superseded"))

    if request.status in {"draft", "confirmed"} and offers:
        issues.append(IntegrityIssue("offers_before_negotiation", "Offers cannot exist before negotiation starts"))
    if request.status == "negotiating" and not offers:
        issues.append(IntegrityIssue("negotiation_without_offers", "Negotiating request must have at least one offer"))
    if len(open_offers) > 1:
        issues.append(IntegrityIssue("multiple_open_offers", "Only one offer may be open at a time"))
    if request.status == "accepted" and len(accepted_offers) != 1:
        issues.append(IntegrityIssue("accepted_offer_count", "Accepted request must have exactly one accepted offer"))
    if request.status != "accepted" and accepted_offers:
        issues.append(IntegrityIssue("accepted_offer_on_unaccepted_request", "An accepted offer requires an accepted request"))
    if request.status == "accepted" and open_offers:
        issues.append(IntegrityIssue("open_offers_after_acceptance", "No open offers may remain after acceptance"))

    return IntegrityReport(
        purchase_request_id=request.id,
        request_status=request.status,
        request_version=request.version,
        is_valid=not issues,
        issues=tuple(issues),
    )
