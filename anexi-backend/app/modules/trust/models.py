import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TrustInteraction(Base):
    __tablename__ = "trust_interactions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    order_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    campaign_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    client_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    product_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    confirmation_status: Mapped[str] = mapped_column(String(32), nullable=False)
    call_duration: Mapped[float] = mapped_column(Float, nullable=False)
    hesitation_score: Mapped[float] = mapped_column(Float, nullable=False)
    interaction_score: Mapped[float] = mapped_column(Float, nullable=False)
    segment: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    recommended_action: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
