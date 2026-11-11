from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PaymentCreate(BaseModel):
    expected_request_version: int = Field(ge=1)


class PaymentRead(BaseModel):
    id: UUID
    purchase_request_id: UUID
    accepted_offer_id: UUID
    paypal_order_id: str
    paypal_capture_id: str | None
    idempotency_key: str
    amount: Decimal
    currency: str
    status: str
    approval_url: str | None
    created_at: datetime
    captured_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
