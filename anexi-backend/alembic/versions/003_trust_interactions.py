"""Create trust_interactions table.

Revision ID: 003_trust_interactions
Revises: 002_tenant_isolation
Create Date: 2026-02-27 00:00:00.000000
"""

from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa


revision: str = "003_trust_interactions"
down_revision: Union[str, None] = "002_tenant_isolation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "trust_interactions",
        sa.Column("id", sa.Uuid(), nullable=False, default=uuid.uuid4),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Uuid(), nullable=False),
        sa.Column("campaign_id", sa.String(length=128), nullable=True),
        sa.Column("confirmation_status", sa.String(length=32), nullable=False),
        sa.Column("call_duration", sa.Float(), nullable=False),
        sa.Column("hesitation_score", sa.Float(), nullable=False),
        sa.Column("interaction_score", sa.Float(), nullable=False),
        sa.Column("segment", sa.String(length=32), nullable=False),
        sa.Column("recommended_action", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_trust_interactions_tenant_id", "trust_interactions", ["tenant_id"], unique=False)
    op.create_index("ix_trust_interactions_campaign_id", "trust_interactions", ["campaign_id"], unique=False)
    op.create_index("ix_trust_interactions_segment", "trust_interactions", ["segment"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_trust_interactions_segment", table_name="trust_interactions")
    op.drop_index("ix_trust_interactions_campaign_id", table_name="trust_interactions")
    op.drop_index("ix_trust_interactions_tenant_id", table_name="trust_interactions")
    op.drop_table("trust_interactions")

