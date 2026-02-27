"""Add optional context fields to trust_interactions.

Revision ID: 004_trust_ctx_fields
Revises: 003_trust_interactions
Create Date: 2026-02-27 00:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "004_trust_ctx_fields"
down_revision: Union[str, None] = "003_trust_interactions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("trust_interactions")}
    if "client_name" not in columns:
        op.add_column("trust_interactions", sa.Column("client_name", sa.String(length=128), nullable=True))
    if "product_name" not in columns:
        op.add_column("trust_interactions", sa.Column("product_name", sa.String(length=256), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("trust_interactions")}
    if "product_name" in columns:
        op.drop_column("trust_interactions", "product_name")
    if "client_name" in columns:
        op.drop_column("trust_interactions", "client_name")
