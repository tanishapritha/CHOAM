"""Add immutable-style purchase audit events."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0007_audit_events"
down_revision = "0006_paypal_payments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("purchase_request_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_role", sa.String(length=16), nullable=False),
        sa.Column("actor_authenticated", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("entity_type", sa.String(length=32), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=False),
        sa.Column("request_version", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=16), nullable=False, server_default="api"),
        sa.Column("details", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "actor_role IN ('buyer', 'seller', 'system')",
            name="ck_audit_events_actor_role",
        ),
        sa.CheckConstraint(
            "source IN ('api', 'mcp', 'system')",
            name="ck_audit_events_source",
        ),
        sa.CheckConstraint("request_version >= 1", name="ck_audit_events_version_positive"),
    )
    op.create_index(
        "ix_audit_events_request_created",
        "audit_events",
        ["purchase_request_id", "created_at"],
    )
    op.create_index("ix_audit_events_entity", "audit_events", ["entity_type", "entity_id"])


def downgrade() -> None:
    op.drop_index("ix_audit_events_entity", table_name="audit_events")
    op.drop_index("ix_audit_events_request_created", table_name="audit_events")
    op.drop_table("audit_events")
