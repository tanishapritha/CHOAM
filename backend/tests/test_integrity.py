from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

from app.services.integrity import evaluate_purchase_integrity


def make_request(status="confirmed", currency="INR", missing_fields=None):
    return SimpleNamespace(
        id=uuid4(),
        status=status,
        version=2,
        currency=currency,
        missing_fields=missing_fields or [],
    )


def make_offer(request_id, *, role="seller", amount=Decimal(1200), currency="INR",
               status="open", parent_id=None, offer_id=None):
    return SimpleNamespace(
        id=offer_id or uuid4(),
        purchase_request_id=request_id,
        proposer_role=role,
        amount=amount,
        currency=currency,
        status=status,
        in_reply_to_offer_id=parent_id,
    )


def test_confirmed_request_without_offers_is_valid():
    request = make_request()
    report = evaluate_purchase_integrity(request, [])
    assert report.is_valid is True
    assert report.issues == ()


def test_negotiating_request_requires_an_offer():
    request = make_request(status="negotiating")
    report = evaluate_purchase_integrity(request, [])
    assert "negotiation_without_offers" in {issue.code for issue in report.issues}


def test_offer_currency_must_match_request_budget_currency():
    request = make_request(currency="INR")
    report = evaluate_purchase_integrity(request, [make_offer(request.id, currency="USD")])
    assert "currency_mismatch" in {issue.code for issue in report.issues}


def test_currency_cannot_change_when_budget_currency_is_unknown():
    request = make_request(currency=None, status="negotiating")
    first = make_offer(request.id, currency="INR", status="superseded")
    second = make_offer(request.id, currency="USD")
    report = evaluate_purchase_integrity(request, [first, second])
    assert "offer_currency_changed" in {issue.code for issue in report.issues}


def test_only_one_offer_may_be_open_at_a_time():
    request = make_request(status="negotiating")
    report = evaluate_purchase_integrity(
        request,
        [make_offer(request.id), make_offer(request.id)],
    )
    assert "multiple_open_offers" in {issue.code for issue in report.issues}


def test_accepted_request_requires_one_accepted_offer_and_no_open_offers():
    request = make_request(status="accepted")
    accepted = make_offer(request.id, status="accepted")
    open_offer = make_offer(request.id, status="open")
    report = evaluate_purchase_integrity(request, [accepted, open_offer])
    codes = {issue.code for issue in report.issues}
    assert "open_offers_after_acceptance" in codes


def test_valid_accepted_request_has_exactly_one_accepted_offer():
    request = make_request(status="accepted")
    accepted = make_offer(request.id, status="accepted")
    report = evaluate_purchase_integrity(request, [accepted])
    assert report.is_valid is True


def test_counteroffer_requires_other_party_and_superseded_parent():
    request = make_request(status="negotiating")
    parent = make_offer(request.id, role="seller", status="superseded")
    counter = make_offer(
        request.id, role="buyer", status="open", parent_id=parent.id
    )
    report = evaluate_purchase_integrity(request, [parent, counter])
    assert report.is_valid is True
