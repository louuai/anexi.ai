from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.modules.events.event_types import VALID_EVENT_TYPES

INGESTION_CHANNELS = {"webhook", "polling", "tracking", "internal"}


class StandardEvent(BaseModel):
    event_id: str = Field(min_length=8, max_length=64)
    tenant_id: int = Field(gt=0)
    merchant_id: int = Field(gt=0)
    customer_id: str = Field(min_length=1, max_length=128)
    event_type: str = Field(min_length=3, max_length=64)
    event_payload: dict[str, Any]
    source_platform: str = Field(min_length=2, max_length=64)
    timestamp: datetime
    correlation_id: str = Field(min_length=8, max_length=64)
    trace_id: str = Field(min_length=8, max_length=64)

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in VALID_EVENT_TYPES:
            raise ValueError("Unsupported event_type for canonical schema")
        return normalized

    @field_validator("source_platform")
    @classmethod
    def normalize_source_platform(cls, value: str) -> str:
        return value.strip().lower()


class IngestionRequest(BaseModel):
    event_id: str | None = Field(default=None, min_length=8, max_length=64)
    tenant_id: int | None = Field(default=None, gt=0)
    merchant_id: int | None = Field(default=None, gt=0)
    customer_id: str | None = Field(default=None, min_length=1, max_length=128)
    event_type: str | None = Field(default=None, min_length=3, max_length=64)
    source_platform: str | None = Field(default=None, min_length=2, max_length=64)
    timestamp: datetime | None = None
    correlation_id: str | None = Field(default=None, min_length=8, max_length=64)
    trace_id: str | None = Field(default=None, min_length=8, max_length=64)
    event_payload: dict[str, Any] = Field(default_factory=dict)
    raw_event: dict[str, Any] = Field(default_factory=dict)


class IngestionEnvelope(BaseModel):
    source_channel: str
    payload: IngestionRequest

    @field_validator("source_channel")
    @classmethod
    def validate_source_channel(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in INGESTION_CHANNELS:
            raise ValueError("Unsupported source_channel")
        return normalized


class IngestionResponse(BaseModel):
    accepted: bool
    source_channel: str
    event: StandardEvent


class EventRecordResponse(BaseModel):
    event_id: str
    tenant_id: int
    merchant_id: int
    customer_id: str
    event_type: str
    event_payload: dict[str, Any]
    source_platform: str
    timestamp: datetime
    correlation_id: str
    trace_id: str
    source_channel: str
    ingested_at: datetime

    model_config = {"from_attributes": True}


class EventReplayResponse(BaseModel):
    items: list[EventRecordResponse]
    total: int


class IntegrationConnectRequest(BaseModel):
    shop_url: str | None = None
    api_key: str | None = None
    webhook_secret: str | None = None


class IntegrationStatusItem(BaseModel):
    connector_type: str
    status: str
    connected_at: datetime | None = None
    last_event_at: datetime | None = None
    events_received: int = 0
    webhook_secret: str | None = None
    config: dict[str, Any] = Field(default_factory=dict)


class IntegrationsOverviewResponse(BaseModel):
    items: list[IntegrationStatusItem]
    webhook_url: str
    tracking_script: str
