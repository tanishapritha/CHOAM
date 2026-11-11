from uuid import uuid4

from app.services.audit import record_audit_event


class FakeSession:
    def __init__(self):
        self.added = []

    def add(self, item):
        self.added.append(item)


def test_audit_event_records_claimed_actor_and_authentication_separately():
    session = FakeSession()
    request_id = uuid4()

    event = record_audit_event(
        session,
        purchase_request_id=request_id,
        actor_role="seller",
        actor_authenticated=False,
        action="offer.created",
        entity_type="negotiation_offer",
        entity_id="offer-123",
        request_version=3,
        details={"currency": "INR", "amount": "1200.00"},
    )

    assert session.added == [event]
    assert event.purchase_request_id == request_id
    assert event.actor_role == "seller"
    assert event.actor_authenticated is False
    assert event.request_version == 3
    assert "buyer_access_token" not in event.details
