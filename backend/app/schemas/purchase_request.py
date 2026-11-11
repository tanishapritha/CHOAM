from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PurchaseIntentPreview(BaseModel):
    item_description: str | None = None
    quantity: int | None = Field(default=None, gt=0)
    unit: str | None = None
    budget_amount: Decimal | None = Field(default=None, gt=0)
    currency: str | None = None
    delivery_location: str | None = None
    required_by: str | None = None
    missing_fields: list[str]
    ready_for_confirmation: bool


class PurchaseIntentInput(BaseModel):
    text: str = Field(min_length=5, max_length=4000)


class PurchaseRequestRead(BaseModel):
    id: UUID
    raw_text: str
    item_description: str | None
    quantity: int | None
    unit: str | None
    budget_amount: Decimal | None
    currency: str | None
    delivery_location: str | None
    required_by: str | None
    missing_fields: list[str]
    status: str
    version: int
    created_at: datetime
    confirmed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class PurchaseRequestCreated(PurchaseRequestRead):
    buyer_access_token: str


class ConfirmPurchaseRequest(BaseModel):
    confirm: bool
    expected_version: int = Field(ge=1)
