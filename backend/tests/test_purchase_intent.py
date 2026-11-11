from decimal import Decimal

from app.services.purchase_intent import extract_purchase_intent


def test_extracts_explicit_purchase_fields():
    result = extract_purchase_intent(
        "I need 12 cartons A4 paper, budget INR 8,500, deliver to Nagpur by 2026-12-01"
    )
    assert result.quantity == 12
    assert result.unit == "cartons"
    assert result.budget_amount == Decimal("8500")
    assert result.currency == "INR"
    assert result.delivery_location == "Nagpur"
    assert result.required_by == "2026-12-01"
    assert result.item_description == "A4 paper"
    assert result.ready_for_confirmation is True


def test_ambiguous_request_requires_buyer_review():
    result = extract_purchase_intent("Need some office supplies soon")
    assert result.ready_for_confirmation is False
    assert "quantity" in result.missing_fields
    assert "delivery_location" in result.missing_fields


def test_does_not_invent_a_budget():
    result = extract_purchase_intent("Order 4 boxes of printer paper and deliver to Pune")
    assert result.budget_amount is None
    assert result.currency is None
    assert result.item_description == "printer paper"
