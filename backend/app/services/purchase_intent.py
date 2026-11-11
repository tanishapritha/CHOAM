import re
from decimal import Decimal

from app.schemas.purchase_request import PurchaseIntentPreview

QUANTITY_RE = re.compile(
    r"\b(?:quantity\s*[:=]?\s*)?(\d+)\s+"
    r"(pieces?|units?|items?|boxes?|packs?|cartons?|kg|kgs|g|grams?|"
    r"litres?|liters?|l|metres?|meters?|m|reams?|sets?)\b",
    re.IGNORECASE,
)
MONEY_RE = re.compile(
    r"\b(INR|Rs\.?|₹|USD|\$|EUR|€|GBP|£)\s*([\d,]+(?:\.\d{1,2})?)\b",
    re.IGNORECASE,
)
DATE_RE = re.compile(r"\b(?:by|before|needed by)\s+(\d{4}-\d{2}-\d{2})\b", re.IGNORECASE)
LOCATION_RE = re.compile(
    r"\b(?:deliver|ship|send)\s+(?:it\s+)?to\s+([^,.;]+?)(?=\s+by\s+\d{4}-\d{2}-\d{2}\b|[,.;]|$)",
    re.IGNORECASE
)
FILLER_RE = re.compile(
    r"\b(?:i|we|need|want|please|buy|purchase|order|of|a|an|the|budget|"
    r"deliver|ship|send|it|to|by|before|needed|and)\b",
    re.IGNORECASE,
)


def extract_purchase_intent(text: str) -> PurchaseIntentPreview:
    """Extract explicit fields only; ambiguity remains visible for buyer review."""
    normalized = " ".join(text.split())
    quantity_match = QUANTITY_RE.search(normalized)
    money_match = MONEY_RE.search(normalized)
    date_match = DATE_RE.search(normalized)
    location_match = LOCATION_RE.search(normalized)

    quantity = int(quantity_match.group(1)) if quantity_match else None
    unit = quantity_match.group(2).lower() if quantity_match else None
    currency = None
    budget = None
    if money_match:
        currency_token, amount = money_match.groups()
        currency = {
            "₹": "INR", "rs": "INR", "rs.": "INR", "$": "USD",
            "€": "EUR", "£": "GBP",
        }.get(currency_token.lower(), currency_token.upper())
        budget = Decimal(amount.replace(",", ""))

    remainder = normalized
    for match in (quantity_match, money_match, date_match, location_match):
        if match:
            remainder = remainder.replace(match.group(0), " ", 1)
    item = FILLER_RE.sub(" ", remainder)
    item = re.sub(r"\s+", " ", item).strip(" ,.-") or None

    missing = []
    if not item:
        missing.append("item_description")
    if quantity is None:
        missing.append("quantity")
    if not location_match:
        missing.append("delivery_location")

    return PurchaseIntentPreview(
        item_description=item,
        quantity=quantity,
        unit=unit,
        budget_amount=budget,
        currency=currency,
        delivery_location=location_match.group(1).strip() if location_match else None,
        required_by=date_match.group(1) if date_match else None,
        missing_fields=missing,
        ready_for_confirmation=not missing,
    )
