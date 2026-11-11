from decimal import Decimal

import pytest

from app.services.negotiation import (
    NegotiationState,
    validate_new_offer,
    validate_response,
)


def test_initial_offer_requires_confirmed_request():
    validate_new_offer(NegotiationState("confirmed", 2), "seller", Decimal(1200), None)


def test_offer_cannot_start_before_buyer_confirmation():
    with pytest.raises(ValueError, match="confirmed"):
        validate_new_offer(NegotiationState("draft", 1), "seller", Decimal(1200), None)


def test_counteroffer_must_come_from_other_party():
    with pytest.raises(ValueError, match="other party"):
        validate_new_offer(NegotiationState("negotiating", 3), "seller", Decimal(1100), "seller")


def test_counteroffer_from_other_party_is_valid():
    validate_new_offer(NegotiationState("negotiating", 3), "buyer", Decimal(1000), "seller")


def test_party_cannot_accept_own_offer():
    with pytest.raises(ValueError, match="own offer"):
        validate_response(NegotiationState("negotiating", 3), "open", "buyer", "buyer")


def test_only_open_offer_can_be_accepted():
    with pytest.raises(ValueError, match="open offers"):
        validate_response(NegotiationState("negotiating", 3), "superseded", "seller", "buyer")


def test_acceptance_requires_negotiating_state():
    with pytest.raises(ValueError, match="not in negotiation"):
        validate_response(NegotiationState("confirmed", 2), "open", "seller", "buyer")
