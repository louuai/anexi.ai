from datetime import datetime

from sqlalchemy.orm import Session

from app.modules.events.models import EventRecord


class TimelineRepository:
    def __init__(self, db: Session):
        self.db = db

    def customer_events(
        self,
        tenant_id: int,
        customer_id: str,
        merchant_id: int | None = None,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        limit: int = 1000,
    ) -> list[EventRecord]:
        query = self.db.query(EventRecord).filter(
            EventRecord.tenant_id == tenant_id,
            EventRecord.customer_id == customer_id,
        )
        if merchant_id is not None:
            query = query.filter(EventRecord.merchant_id == merchant_id)
        if start_at is not None:
            query = query.filter(EventRecord.timestamp >= start_at)
        if end_at is not None:
            query = query.filter(EventRecord.timestamp <= end_at)
        return (
            query.order_by(EventRecord.timestamp.asc(), EventRecord.id.asc())
            .limit(limit)
            .all()
        )

