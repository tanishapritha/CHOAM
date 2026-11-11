from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

Role = Literal["buyer", "seller"]


@dataclass(frozen=True)
class NegotiationState:
    request_status: str
    request_version: int


def validate_new_offer(
    state: NegotiationState,
    actor_role: Role,
    amount: Decimal,
    reply_to_role: Role | None,
) -> None:
    if state.request_status not in {"confirmed", "negotiating"}:
        raise ValueError("Offers require a confirmed purchase request")
    if amount <= 0:
        raise ValueError("Offer amount must be greater than zero")
    if reply_to_role is not None and reply_to_role == actor_role:
        raise ValueError("A counteroffer must respond to the other party's offer")


def validate_response(
    state: NegotiationState,
    offer_status: str,
    proposer_role: Role,
    actor_role: Role,
) -> None:
    if state.request_status != "negotiating":
        raise ValueError("The purchase request is not in negotiation")
    if offer_status != "open":
        raise ValueError("Only open offers can be accepted or rejected")
    if proposer_role == actor_role:
        raise ValueError("You cannot respond to your own offer")
