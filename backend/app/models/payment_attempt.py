from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PaymentAttempt(Base):
    __tablename__ = "payment_attempts"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_payment_attempts_idempotency_key"),
        Index("ix_payment_attempts_request_created", "purchase_request_id", "created_at"),
        CheckConstraint("amount > 0", name="ck_payment_attempts_amount_positive"),
        CheckConstraint(
            "status IN ('created', 'captured', 'failed')",
            name="ck_payment_attempts_status",
        ),
        CheckConstraint("currency ~ '^[A-Z]{3}$'", name="ck_payment_attempts_currency"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    purchase_request_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("purchase_requests.id", ondelete="CASCADE"),
        nullable=False,
    )
    accepted_offer_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("negotiation_offers.id", ondelete="RESTRICT"),
        nullable=False,
    )
    paypal_order_id: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    paypal_capture_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    status: Mapped[str] = mapped_column(String(12), nullable=False, default="created")
    approval_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    captured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
