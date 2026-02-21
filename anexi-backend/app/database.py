import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

# Use the standard PostgreSQL port (5432) by default and allow override via env var.
# The original string pointed to port 3306 (MySQL), which causes connection failures
# when a PostgreSQL server is running on its usual port.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:louaiouni05062001@localhost:5433/anexi",
)

# pool_pre_ping keeps connections healthy across restarts; future=True uses new SQLAlchemy 2.0 engine API.
engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)

# Explicitly disable autocommit/autoflush to avoid accidental partial writes.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

Base = declarative_base()


def get_db():
    """Yield a scoped session and ensure it is closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
