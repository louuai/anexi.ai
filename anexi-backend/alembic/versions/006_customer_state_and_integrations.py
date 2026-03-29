"""Add customer_state cache and merchant_integrations tables.

Revision ID: 006_customer_state_integrations
Revises: 005_event_store
Create Date: 2026-03-07 13:10:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "006_customer_state_integrations"
down_revision: Union[str, None] = "005_event_store"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "customer_state" not in tables:
        op.create_table(
            "customer_state",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("tenant_id", sa.Integer(), nullable=False),
            sa.Column("merchant_id", sa.Integer(), nullable=False),
            sa.Column("customer_id", sa.String(length=128), nullable=False),
            sa.Column("total_orders", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("total_refunds", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("trust_score", sa.Float(), nullable=False, server_default="50"),
            sa.Column("last_event", sa.String(length=64), nullable=False, server_default="unknown"),
            sa.Column("last_event_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.UniqueConstraint("tenant_id", "merchant_id", "customer_id", name="uq_customer_state_scope"),
        )
        op.create_index("ix_customer_state_tenant_id", "customer_state", ["tenant_id"])
        op.create_index("ix_customer_state_merchant_id", "customer_state", ["merchant_id"])
        op.create_index("ix_customer_state_customer_id", "customer_state", ["customer_id"])
        op.create_index("ix_customer_state_last_event_at", "customer_state", ["last_event_at"])
        op.create_index("ix_customer_state_updated_at", "customer_state", ["updated_at"])

    if "merchant_integrations" not in tables:
        op.create_table(
            "merchant_integrations",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("tenant_id", sa.Integer(), nullable=False),
            sa.Column("merchant_id", sa.Integer(), nullable=False),
            sa.Column("connector_type", sa.String(length=32), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="not_connected"),
            sa.Column("connected_at", sa.DateTime(), nullable=True),
            sa.Column("last_event_at", sa.DateTime(), nullable=True),
            sa.Column("events_received", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("webhook_secret", sa.String(length=128), nullable=True),
            sa.Column("config", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.UniqueConstraint("tenant_id", "merchant_id", "connector_type", name="uq_merchant_integration_scope"),
        )
        op.create_index("ix_merchant_integrations_tenant_id", "merchant_integrations", ["tenant_id"])
        op.create_index("ix_merchant_integrations_merchant_id", "merchant_integrations", ["merchant_id"])
        op.create_index("ix_merchant_integrations_connector_type", "merchant_integrations", ["connector_type"])
        op.create_index("ix_merchant_integrations_last_event_at", "merchant_integrations", ["last_event_at"])
        op.create_index("ix_merchant_integrations_updated_at", "merchant_integrations", ["updated_at"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "merchant_integrations" in tables:
        op.drop_table("merchant_integrations")
    if "customer_state" in tables:
        op.drop_table("customer_state")

