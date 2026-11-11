from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Role = Literal["buyer", "seller"]
Currency = Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")]


class NegotiationOfferCreate(BaseModel):
    actor_role: Role
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    currency: Currency
    message: str | None = Field(default=None, max_length=2000)
    expected_request_version: int = Field(ge=1)
    in_reply_to_offer_id: UUID | None = None


class NegotiationResponse(BaseModel):
    actor_role: Role
    expected_request_version: int = Field(ge=1)


class NegotiationOfferRead(BaseModel):
    id: UUID
    purchase_request_id: UUID
    proposer_role: Role
    amount: Decimal
    currency: str
    message: str | None
    in_reply_to_offer_id: UUID | None
    status: Literal["open", "accepted", "rejected", "superseded"]
    created_at: datetime
    responded_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
