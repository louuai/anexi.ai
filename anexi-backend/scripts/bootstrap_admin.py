import os
import sys

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database import Base, SessionLocal, engine
from app.models import User
from app.utils.security import hash_password


def _env(name: str, default: str) -> str:
    return os.getenv(name, default).strip()


def _allocate_user_id(db) -> int:
    next_id = db.execute(
        text("SELECT nextval(pg_get_serial_sequence('users', 'id'))")
    ).scalar()
    return int(next_id)


def main() -> int:
    email = _env("DEFAULT_ADMIN_EMAIL", "admin@anexi.local").lower()
    password = os.getenv("DEFAULT_ADMIN_PASSWORD", "Admin12345!")
    full_name = _env("DEFAULT_ADMIN_FULL_NAME", "Platform Admin")
    role = _env("DEFAULT_ADMIN_ROLE", "founder").lower()

    if not email or not password:
        print("bootstrap_admin: skipped because admin email/password is empty")
        return 0

    if len(password) < 8:
        print("bootstrap_admin: password must be at least 8 characters", file=sys.stderr)
        return 1

    # Monolith mode may reach this script before the API process creates tables.
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        user = db.query(User).filter_by(email=email).first()
        hashed = hash_password(password)

        if user is None:
            user_id = _allocate_user_id(db)
            user = User(
                id=user_id,
                tenant_id=user_id,
                email=email,
                password_hash=hashed,
                full_name=full_name,
                role=role,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"bootstrap_admin: created {email} with role={user.role} id={user.id}")
            return 0

        changed = False
        if user.role != role:
            user.role = role
            changed = True
        if full_name and user.full_name != full_name:
            user.full_name = full_name
            changed = True
        if user.tenant_id is None:
            user.tenant_id = user.id
            changed = True

        # Keep password in sync so the documented bootstrap credentials always work.
        user.password_hash = hashed
        changed = True

        if changed:
            db.commit()
            db.refresh(user)

        print(f"bootstrap_admin: ensured {email} with role={user.role} id={user.id}")
        return 0
    except SQLAlchemyError as exc:
        db.rollback()
        print(f"bootstrap_admin: failed with {exc.__class__.__name__}: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
