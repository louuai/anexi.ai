from datetime import datetime

from pydantic import BaseModel


class TimelineEvent(BaseModel):
    timestamp: datetime
    event_type: str
    source_platform: str
    correlation_id: str
    trace_id: str
    event_payload: dict


class CustomerTimeline(BaseModel):
    tenant_id: int
    merchant_id: int | None = None
    customer_id: str
    items: list[TimelineEvent]
    total: int

