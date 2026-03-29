import os
import subprocess
import sys

from sqlalchemy import create_engine, inspect, text


def run_cmd(args):
    proc = subprocess.run(args, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.stdout.write(proc.stdout)
        sys.stderr.write(proc.stderr)
        raise SystemExit(proc.returncode)
    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)


TENANT_TABLES = [
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


def _has_table(insp, table_name):
    return table_name in insp.get_table_names()


def _has_column(insp, table_name, column_name):
    if not _has_table(insp, table_name):
        return False
    return any(col["name"] == column_name for col in insp.get_columns(table_name))


def _has_index(insp, table_name, index_name):
    if not _has_table(insp, table_name):
        return False
    return any(idx["name"] == index_name for idx in insp.get_indexes(table_name))


def ensure_schema_compat(engine):
    with engine.begin() as conn:
        insp = inspect(conn)

        if _has_table(insp, "users"):
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(30)"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url TEXT"))
            conn.execute(
                text(
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS updated_at "
                    "TIMESTAMP WITHOUT TIME ZONE DEFAULT now()"
                )
            )

        insp = inspect(conn)
        for table in TENANT_TABLES:
            if _has_table(insp, table):
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS tenant_id INTEGER"))

        conn.execute(text("UPDATE users SET tenant_id = id WHERE tenant_id IS NULL"))
        conn.execute(
            text(
                """
                UPDATE user_profiles up
                SET tenant_id = u.tenant_id
                FROM users u
                WHERE up.user_id = u.id
                  AND up.tenant_id IS NULL
                """
            )
        )
        conn.execute(
            text(
                """
                UPDATE boutiques b
                SET tenant_id = u.tenant_id
                FROM users u
                WHERE b.owner_id = u.id
                  AND b.tenant_id IS NULL
                """
            )
        )
        conn.execute(
            text(
                """
                UPDATE customers c
                SET tenant_id = b.tenant_id
                FROM boutiques b
                WHERE c.boutique_id = b.id
                  AND c.tenant_id IS NULL
                """
            )
        )
        conn.execute(
            text(
                """
                UPDATE orders o
                SET tenant_id = b.tenant_id
                FROM boutiques b
                WHERE o.boutique_id = b.id
                  AND o.tenant_id IS NULL
                """
            )
        )
        conn.execute(
            text(
                """
                UPDATE calls c
                SET tenant_id = o.tenant_id
                FROM orders o
                WHERE c.order_id = o.id
                  AND c.tenant_id IS NULL
                """
            )
        )
        conn.execute(
            text(
                """
                UPDATE ads_insights ai
                SET tenant_id = b.tenant_id
                FROM boutiques b
                WHERE ai.boutique_id = b.id
                  AND ai.tenant_id IS NULL
                """
            )
        )
        conn.execute(
            text(
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
            text(
                """
                UPDATE ai_decisions
                SET tenant_id = COALESCE((SELECT MIN(tenant_id) FROM users), 1)
                WHERE tenant_id IS NULL
                """
            )
        )
        if _has_table(insp, "payments"):
            conn.execute(
                text(
                    """
                    UPDATE payments p
                    SET tenant_id = u.tenant_id
                    FROM users u
                    WHERE p.user_id = u.id
                      AND p.tenant_id IS NULL
                    """
                )
            )

        insp = inspect(conn)
        for table in TENANT_TABLES:
            if not _has_table(insp, table) or not _has_column(insp, table, "tenant_id"):
                continue
            index_name = f"ix_{table}_tenant_id"
            if not _has_index(insp, table, index_name):
                conn.execute(text(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table} (tenant_id)"))
            null_count = conn.execute(
                text(f"SELECT COUNT(*) FROM {table} WHERE tenant_id IS NULL")
            ).scalar()
            if int(null_count or 0) == 0:
                conn.execute(text(f"ALTER TABLE {table} ALTER COLUMN tenant_id SET NOT NULL"))


def main():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL is required")

    engine = create_engine(database_url, future=True)
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    has_user_tables = "users" in tables
    has_alembic_table = "alembic_version" in tables

    if has_user_tables and not has_alembic_table:
        # Legacy databases can have the initial schema without tenant columns.
        # Stamp the initial revision so `upgrade head` still executes follow-up migrations.
        print("Existing schema detected without alembic_version. Stamping 001_initial...")
        run_cmd(["alembic", "stamp", "001_initial"])

    print("Applying migrations...")
    run_cmd(["alembic", "upgrade", "head"])
    print("Ensuring schema compatibility...")
    ensure_schema_compat(engine)

    with engine.connect() as conn:
        current = conn.execute(text("SELECT version_num FROM alembic_version LIMIT 1")).scalar()
    print(f"Migration complete. alembic_version={current}")


if __name__ == "__main__":
    main()
