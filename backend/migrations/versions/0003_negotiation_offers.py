"""Add buyer-seller negotiation offer history."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003_negotiation_offers"
down_revision = "0002_purchase_requests"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "negotiation_offers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "purchase_request_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("purchase_requests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("proposer_role", sa.String(length=10), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column(
            "in_reply_to_offer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("negotiation_offers.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("status", sa.String(length=12), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_negotiation_offers_request_created",
        "negotiation_offers",
        ["purchase_request_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_negotiation_offers_request_created", table_name="negotiation_offers")
    op.drop_table("negotiation_offers")
