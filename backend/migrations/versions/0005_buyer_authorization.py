"""Add buyer bearer credential storage."""

from alembic import op
import sqlalchemy as sa

revision = "0005_buyer_authorization"
down_revision = "0004_integrity_constraints"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "purchase_requests",
        sa.Column("buyer_token_hash", sa.String(length=64), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("purchase_requests", "buyer_token_hash")
