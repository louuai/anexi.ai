"""Add tenant isolation columns and backfill data.

Revision ID: 002_tenant_isolation
Revises: 001_initial
Create Date: 2026-02-24 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "002_tenant_isolation"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TABLES = [
    "users",
    "user_profiles",
    "boutiques",
    "customers",
    "orders",
    "calls",
    "ai_decisions",
    "ads_insights",
    "payments",
]


def _has_table(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _has_column(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    if not _has_table(inspector, table_name):
        return False
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


def _has_index(inspector: sa.Inspector, table_name: str, index_name: str) -> bool:
    if not _has_table(inspector, table_name):
        return False
    return any(idx["name"] == index_name for idx in inspector.get_indexes(table_name))


def _set_not_null_if_possible(table_name: str) -> None:
    conn = op.get_bind()
    null_count = conn.execute(
        sa.text(f"SELECT COUNT(*) FROM {table_name} WHERE tenant_id IS NULL")
    ).scalar()
    if int(null_count or 0) == 0:
        op.alter_column(table_name, "tenant_id", existing_type=sa.Integer(), nullable=False)


def _fallback_tenant_id() -> int:
    conn = op.get_bind()
    tenant_id = conn.execute(
        sa.text("SELECT COALESCE(MIN(tenant_id), MIN(id), 1) FROM users")
    ).scalar()
    return int(tenant_id or 1)


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    for table in TABLES:
        if _has_table(inspector, table) and not _has_column(inspector, table, "tenant_id"):
            op.add_column(table, sa.Column("tenant_id", sa.Integer(), nullable=True))

    inspector = sa.inspect(conn)
    if _has_table(inspector, "users") and _has_column(inspector, "users", "tenant_id"):
        conn.execute(sa.text("UPDATE users SET tenant_id = id WHERE tenant_id IS NULL"))

    if _has_table(inspector, "user_profiles") and _has_column(inspector, "user_profiles", "tenant_id"):
        conn.execute(
            sa.text(
                """
                UPDATE user_profiles up
                SET tenant_id = u.tenant_id
                FROM users u
                WHERE up.user_id = u.id
                  AND up.tenant_id IS NULL
                """
            )
        )

    if _has_table(inspector, "boutiques") and _has_column(inspector, "boutiques", "tenant_id"):
        conn.execute(
            sa.text(
                """
                UPDATE boutiques b
                SET tenant_id = u.tenant_id
                FROM users u
                WHERE b.owner_id = u.id
                  AND b.tenant_id IS NULL
                """
            )
        )

    if _has_table(inspector, "customers") and _has_column(inspector, "customers", "tenant_id"):
        conn.execute(
            sa.text(
                """
                UPDATE customers c
                SET tenant_id = b.tenant_id
                FROM boutiques b
                WHERE c.boutique_id = b.id
                  AND c.tenant_id IS NULL
                """
            )
        )

    if _has_table(inspector, "orders") and _has_column(inspector, "orders", "tenant_id"):
        conn.execute(
            sa.text(
                """
                UPDATE orders o
                SET tenant_id = b.tenant_id
                FROM boutiques b
                WHERE o.boutique_id = b.id
                  AND o.tenant_id IS NULL
                """
            )
        )

    if _has_table(inspector, "calls") and _has_column(inspector, "calls", "tenant_id"):
        conn.execute(
            sa.text(
                """
                UPDATE calls c
                SET tenant_id = o.tenant_id
                FROM orders o
                WHERE c.order_id = o.id
                  AND c.tenant_id IS NULL
                """
            )
        )

    if _has_table(inspector, "ai_decisions") and _has_column(inspector, "ai_decisions", "tenant_id"):
        conn.execute(
            sa.text(
                """
                UPDATE ai_decisions d
                SET tenant_id = o.tenant_id
                FROM orders o
                WHERE d.source_type = 'order'
                  AND d.source_id = o.id
                  AND d.tenant_id IS NULL
                """
            )
        )
        conn.execute(
            sa.text(
                """
                UPDATE ai_decisions
                SET tenant_id = (
                    SELECT tenant_id
                    FROM users
                    WHERE tenant_id IS NOT NULL
                    ORDER BY id
                    LIMIT 1
                )
                WHERE tenant_id IS NULL
                """
            )
        )

    if _has_table(inspector, "ads_insights") and _has_column(inspector, "ads_insights", "tenant_id"):
        conn.execute(
            sa.text(
                """
                UPDATE ads_insights ai
                SET tenant_id = b.tenant_id
                FROM boutiques b
                WHERE ai.boutique_id = b.id
                  AND ai.tenant_id IS NULL
                """
            )
        )

    if _has_table(inspector, "payments") and _has_column(inspector, "payments", "tenant_id"):
        conn.execute(
            sa.text(
                """
                UPDATE payments p
                SET tenant_id = u.tenant_id
                FROM users u
                WHERE p.user_id = u.id
                  AND p.tenant_id IS NULL
                """
            )
        )

    fallback_tenant = _fallback_tenant_id()
    inspector = sa.inspect(conn)
    for table in TABLES:
        if _has_table(inspector, table) and _has_column(inspector, table, "tenant_id"):
            conn.execute(
                sa.text(f"UPDATE {table} SET tenant_id = :tenant_id WHERE tenant_id IS NULL"),
                {"tenant_id": fallback_tenant},
            )

    inspector = sa.inspect(conn)
    for table in TABLES:
        if _has_table(inspector, table) and _has_column(inspector, table, "tenant_id"):
            _set_not_null_if_possible(table)
            index_name = f"ix_{table}_tenant_id"
            if not _has_index(inspector, table, index_name):
                op.create_index(index_name, table, ["tenant_id"], unique=False)


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    for table in reversed(TABLES):
        if not _has_table(inspector, table):
            continue
        index_name = f"ix_{table}_tenant_id"
        if _has_index(inspector, table, index_name):
            op.drop_index(index_name, table_name=table)
        if _has_column(inspector, table, "tenant_id"):
            op.drop_column(table, "tenant_id")
