from datetime import datetime, timedelta
import secrets

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import User
from app.modules.events.ingestion.normalizers import normalize_event
from app.modules.events.repository import EventStoreRepository
from app.modules.events.schemas import (
    EventReplayResponse,
    IntegrationConnectRequest,
    IntegrationsOverviewResponse,
    IntegrationStatusItem,
    IngestionEnvelope,
    IngestionResponse,
)
from app.modules.events.stream import get_event_stream
from app.utils.tenant import require_tenant_id


def ingest_event(
    db: Session,
    current_user: User,
    envelope: IngestionEnvelope,
) -> IngestionResponse:
    tenant_id = require_tenant_id(current_user.tenant_id)
    requested_tenant = envelope.payload.tenant_id
    if requested_tenant is not None and int(requested_tenant) != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cross-tenant event ingestion is not allowed",
        )

    normalized = normalize_event(envelope=envelope, current_user=current_user)
    if normalized.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid tenant attribution",
        )

    repo = EventStoreRepository(db)
    repo.append(source_channel=envelope.source_channel, event=normalized)
    get_event_stream().publish(normalized)

    return IngestionResponse(
        accepted=True,
        source_channel=envelope.source_channel,
        event=normalized,
    )


def list_events_by_customer(
    db: Session,
    tenant_id: int,
    customer_id: str,
    limit: int,
):
    repo = EventStoreRepository(db)
    return repo.by_customer(tenant_id=tenant_id, customer_id=customer_id, limit=limit)


def list_events_by_merchant(
    db: Session,
    tenant_id: int,
    merchant_id: int,
    limit: int,
):
    repo = EventStoreRepository(db)
    return repo.by_merchant(tenant_id=tenant_id, merchant_id=merchant_id, limit=limit)


def replay_events(
    db: Session,
    tenant_id: int,
    start_at: datetime | None,
    end_at: datetime | None,
    merchant_id: int | None,
    customer_id: str | None,
    limit: int,
) -> EventReplayResponse:
    effective_end = end_at or datetime.utcnow()
    effective_start = start_at or (effective_end - timedelta(days=7))
    if effective_start > effective_end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_at must be <= end_at",
        )

    repo = EventStoreRepository(db)
    rows = repo.replay(
        tenant_id=tenant_id,
        start_at=effective_start,
        end_at=effective_end,
        merchant_id=merchant_id,
        customer_id=customer_id,
        limit=limit,
    )
    return EventReplayResponse(items=rows, total=len(rows))


_DEFAULT_CONNECTORS = [
    "shopify",
    "woocommerce",
    "webhook",
    "api",
    "tracking_script",
]


def get_integrations_overview(db: Session, tenant_id: int, merchant_id: int) -> IntegrationsOverviewResponse:
    repo = EventStoreRepository(db)
    current = {
        row.connector_type: row
        for row in repo.list_merchant_integrations(tenant_id=tenant_id, merchant_id=merchant_id)
    }
    items: list[IntegrationStatusItem] = []
    for connector in _DEFAULT_CONNECTORS:
        row = current.get(connector)
        if row is None:
            items.append(
                IntegrationStatusItem(
                    connector_type=connector,
                    status="not_connected",
                    connected_at=None,
                    last_event_at=None,
                    events_received=0,
                    webhook_secret=None,
                    config={},
                )
            )
            continue
        items.append(
            IntegrationStatusItem(
                connector_type=row.connector_type,
                status=row.status,
                connected_at=row.connected_at,
                last_event_at=row.last_event_at,
                events_received=int(row.events_received or 0),
                webhook_secret=row.webhook_secret,
                config=row.config or {},
            )
        )

    return IntegrationsOverviewResponse(
        items=items,
        webhook_url="https://api.anexi.ai/events/webhook",
        tracking_script='<script src="https://cdn.anexi.ai/pixel.js"></script>',
    )


def connect_integration(
    db: Session,
    tenant_id: int,
    merchant_id: int,
    connector_type: str,
    payload: IntegrationConnectRequest,
) -> IntegrationStatusItem:
    normalized = connector_type.strip().lower()
    if normalized not in _DEFAULT_CONNECTORS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported connector type")

    config: dict = {}
    webhook_secret = payload.webhook_secret
    if normalized == "shopify":
        if not payload.shop_url or not payload.api_key or not payload.webhook_secret:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="shop_url, api_key and webhook_secret are required for Shopify",
            )
        config = {
            "shop_url": payload.shop_url.strip(),
            "api_key": payload.api_key.strip(),
            "webhook_active": True,
        }
    elif normalized == "webhook":
        webhook_secret = payload.webhook_secret or secrets.token_hex(16)
        config = {"webhook_active": True}
    elif normalized == "tracking_script":
        config = {"pixel_active": True}
    elif normalized == "woocommerce":
        if payload.shop_url:
            config["shop_url"] = payload.shop_url.strip()
    elif normalized == "api":
        config = {"api_enabled": True}

    repo = EventStoreRepository(db)
    row = repo.upsert_merchant_integration(
        tenant_id=tenant_id,
        merchant_id=merchant_id,
        connector_type=normalized,
        status="connected",
        config=config,
        webhook_secret=webhook_secret,
    )
    return IntegrationStatusItem(
        connector_type=row.connector_type,
        status=row.status,
        connected_at=row.connected_at,
        last_event_at=row.last_event_at,
        events_received=int(row.events_received or 0),
        webhook_secret=row.webhook_secret,
        config=row.config or {},
    )
