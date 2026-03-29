"""Create append-only event_store table.

Revision ID: 005_event_store
Revises: 004_trust_ctx_fields
Create Date: 2026-03-07 11:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "005_event_store"
down_revision: Union[str, None] = "004_trust_ctx_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "event_store" in tables:
        return

    op.create_table(
        "event_store",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("event_id", sa.String(length=64), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("merchant_id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.String(length=128), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("event_payload", sa.JSON(), nullable=False),
        sa.Column("source_platform", sa.String(length=64), nullable=False),
        sa.Column("source_channel", sa.String(length=32), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("correlation_id", sa.String(length=64), nullable=False),
        sa.Column("trace_id", sa.String(length=64), nullable=False),
        sa.Column("ingested_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("event_id", name="uq_event_store_event_id"),
    )
    op.create_index("ix_event_store_event_id", "event_store", ["event_id"])
    op.create_index("ix_event_store_tenant_id", "event_store", ["tenant_id"])
    op.create_index("ix_event_store_merchant_id", "event_store", ["merchant_id"])
    op.create_index("ix_event_store_customer_id", "event_store", ["customer_id"])
    op.create_index("ix_event_store_event_type", "event_store", ["event_type"])
    op.create_index("ix_event_store_source_platform", "event_store", ["source_platform"])
    op.create_index("ix_event_store_source_channel", "event_store", ["source_channel"])
    op.create_index("ix_event_store_timestamp", "event_store", ["timestamp"])
    op.create_index("ix_event_store_correlation_id", "event_store", ["correlation_id"])
    op.create_index("ix_event_store_trace_id", "event_store", ["trace_id"])
    op.create_index("ix_event_store_ingested_at", "event_store", ["ingested_at"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "event_store" not in tables:
        return
    op.drop_table("event_store")

