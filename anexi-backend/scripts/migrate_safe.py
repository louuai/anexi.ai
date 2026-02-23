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
        print("Existing schema detected without alembic_version. Stamping head...")
        run_cmd(["alembic", "stamp", "head"])

    print("Applying migrations...")
    run_cmd(["alembic", "upgrade", "head"])

    with engine.connect() as conn:
        current = conn.execute(text("SELECT version_num FROM alembic_version LIMIT 1")).scalar()
    print(f"Migration complete. alembic_version={current}")


if __name__ == "__main__":
    main()

