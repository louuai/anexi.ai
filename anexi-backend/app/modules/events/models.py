from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class EventRecord(Base):
    __tablename__ = "event_store"
    __table_args__ = (
        UniqueConstraint("event_id", name="uq_event_store_event_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    merchant_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    event_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    source_platform: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_channel: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    correlation_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    trace_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class CustomerState(Base):
    __tablename__ = "customer_state"
    __table_args__ = (
        UniqueConstraint("tenant_id", "merchant_id", "customer_id", name="uq_customer_state_scope"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    merchant_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    total_orders: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_refunds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    trust_score: Mapped[float] = mapped_column(Float, nullable=False, default=50.0)
    last_event: Mapped[str] = mapped_column(String(64), nullable=False, default="unknown")
    last_event_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)


class MerchantIntegration(Base):
    __tablename__ = "merchant_integrations"
    __table_args__ = (
        UniqueConstraint("tenant_id", "merchant_id", "connector_type", name="uq_merchant_integration_scope"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    merchant_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    connector_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="not_connected")
    connected_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_event_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    events_received: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    webhook_secret: Mapped[str | None] = mapped_column(String(128), nullable=True)
    config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)
