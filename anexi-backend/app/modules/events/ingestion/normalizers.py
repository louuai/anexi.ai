from datetime import datetime
from uuid import uuid4

from opentelemetry import trace

from app.models import User
from app.observability.context import get_correlation_id
from app.modules.events.event_types import EVENT_TYPE_ALIASES
from app.modules.events.schemas import IngestionEnvelope, StandardEvent


def _trace_id_or_generated() -> str:
    span = trace.get_current_span()
    span_ctx = span.get_span_context() if span else None
    if span_ctx and span_ctx.is_valid:
        return f"{span_ctx.trace_id:032x}"
    return uuid4().hex


def _canonical_event_type(raw_type: str | None, payload: dict) -> str:
    candidate = str(raw_type or payload.get("event_type") or payload.get("type") or "").strip().lower()
    if candidate in EVENT_TYPE_ALIASES:
        return EVENT_TYPE_ALIASES[candidate]
    return candidate


def normalize_event(envelope: IngestionEnvelope, current_user: User) -> StandardEvent:
    payload = envelope.payload
    raw = payload.raw_event or {}

    tenant_id = int(payload.tenant_id or current_user.tenant_id or 0)
    merchant_id = int(payload.merchant_id or current_user.id or 0)
    customer_id = str(
        payload.customer_id
        or raw.get("customer_id")
        or raw.get("customer")
        or raw.get("customer_email")
        or raw.get("customer_phone")
        or "anonymous"
    )[:128]
    event_payload = payload.event_payload or raw

    normalized = StandardEvent(
        event_id=str(raw.get("event_id") or payload.event_id or "") or str(uuid4()),
        tenant_id=tenant_id,
        merchant_id=merchant_id,
        customer_id=customer_id,
        event_type=_canonical_event_type(payload.event_type, raw),
        event_payload=event_payload,
        source_platform=str(payload.source_platform or raw.get("source_platform") or raw.get("platform") or "unknown"),
        timestamp=payload.timestamp or datetime.utcnow(),
        correlation_id=payload.correlation_id or get_correlation_id() or str(uuid4()),
        trace_id=payload.trace_id or _trace_id_or_generated(),
    )
    return normalized
