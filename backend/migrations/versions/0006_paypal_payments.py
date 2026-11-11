"""Add PayPal sandbox payment attempts."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0006_paypal_payments"
down_revision = "0005_buyer_authorization"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "payment_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "purchase_request_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("purchase_requests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "accepted_offer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("negotiation_offers.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("paypal_order_id", sa.String(length=80), nullable=False, unique=True),
        sa.Column("paypal_capture_id", sa.String(length=80), nullable=True),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("status", sa.String(length=12), nullable=False, server_default="created"),
        sa.Column("approval_url", sa.String(length=2048), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("idempotency_key", name="uq_payment_attempts_idempotency_key"),
        sa.CheckConstraint("amount > 0", name="ck_payment_attempts_amount_positive"),
        sa.CheckConstraint(
            "status IN ('created', 'captured', 'failed')",
            name="ck_payment_attempts_status",
        ),
        sa.CheckConstraint("currency ~ '^[A-Z]{3}$'", name="ck_payment_attempts_currency"),
    )
    op.create_index(
        "ix_payment_attempts_request_created",
        "payment_attempts",
        ["purchase_request_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_payment_attempts_request_created", table_name="payment_attempts")
    op.drop_table("payment_attempts")
