"""Add database constraints for purchase and offer integrity."""

from alembic import op

revision = "0004_integrity_constraints"
down_revision = "0003_negotiation_offers"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_purchase_requests_status",
        "purchase_requests",
        "status IN ('draft', 'confirmed', 'negotiating', 'accepted')",
    )
    op.create_check_constraint(
        "ck_purchase_requests_version_positive",
        "purchase_requests",
        "version >= 1",
    )
    op.create_check_constraint(
        "ck_negotiation_offers_amount_positive",
        "negotiation_offers",
        "amount > 0",
    )
    op.create_check_constraint(
        "ck_negotiation_offers_proposer_role",
        "negotiation_offers",
        "proposer_role IN ('buyer', 'seller')",
    )
    op.create_check_constraint(
        "ck_negotiation_offers_status",
        "negotiation_offers",
        "status IN ('open', 'accepted', 'rejected', 'superseded')",
    )
    op.create_check_constraint(
        "ck_negotiation_offers_currency",
        "negotiation_offers",
        "currency ~ '^[A-Z]{3}$'",
    )


def downgrade() -> None:
    op.drop_constraint("ck_negotiation_offers_currency", "negotiation_offers", type_="check")
    op.drop_constraint("ck_negotiation_offers_status", "negotiation_offers", type_="check")
    op.drop_constraint("ck_negotiation_offers_proposer_role", "negotiation_offers", type_="check")
    op.drop_constraint("ck_negotiation_offers_amount_positive", "negotiation_offers", type_="check")
    op.drop_constraint("ck_purchase_requests_version_positive", "purchase_requests", type_="check")
    op.drop_constraint("ck_purchase_requests_status", "purchase_requests", type_="check")
