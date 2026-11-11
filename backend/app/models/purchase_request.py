from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, Index, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PurchaseRequest(Base):
    __tablename__ = "purchase_requests"
    __table_args__ = (
        Index("ix_purchase_requests_status", "status"),
        CheckConstraint(
            "status IN ('draft', 'confirmed', 'negotiating', 'accepted')",
            name="ck_purchase_requests_status",
        ),
        CheckConstraint("version >= 1", name="ck_purchase_requests_version_positive"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    item_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(40), nullable=True)
    budget_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    delivery_location: Mapped[str | None] = mapped_column(String(240), nullable=True)
    required_by: Mapped[str | None] = mapped_column(String(10), nullable=True)
    missing_fields: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
