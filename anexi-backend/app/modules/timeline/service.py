from datetime import datetime

from sqlalchemy.orm import Session

from app.modules.timeline.repository import TimelineRepository
from app.modules.timeline.schemas import CustomerTimeline, TimelineEvent


def build_customer_timeline(
    db: Session,
    tenant_id: int,
    customer_id: str,
    merchant_id: int | None = None,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    limit: int = 1000,
) -> CustomerTimeline:
    repo = TimelineRepository(db)
    rows = repo.customer_events(
        tenant_id=tenant_id,
        customer_id=customer_id,
        merchant_id=merchant_id,
        start_at=start_at,
        end_at=end_at,
        limit=limit,
    )
    items = [
        TimelineEvent(
            timestamp=row.timestamp,
            event_type=row.event_type,
            source_platform=row.source_platform,
            correlation_id=row.correlation_id,
            trace_id=row.trace_id,
            event_payload=row.event_payload,
        )
        for row in rows
    ]
    merchant = rows[0].merchant_id if rows else merchant_id
    return CustomerTimeline(
        tenant_id=tenant_id,
        merchant_id=merchant,
        customer_id=customer_id,
        items=items,
        total=len(items),
    )

