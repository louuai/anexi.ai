from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.modules.events.schemas import EventRecordResponse, IngestionEnvelope, IngestionResponse, IntegrationConnectRequest
from app.modules.events.service import (
    connect_integration,
    get_integrations_overview,
    ingest_event,
    list_events_by_customer,
    list_events_by_merchant,
    replay_events,
)
from app.routes.auth import get_current_user
from app.utils.tenant import require_tenant_id

router = APIRouter(tags=["Events"])


@router.post("/events/ingestion/webhooks", response_model=IngestionResponse)
def ingest_webhook_event(
    envelope: IngestionEnvelope,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    envelope.source_channel = "webhook"
    return ingest_event(db=db, current_user=current_user, envelope=envelope)


@router.post("/events/webhook", response_model=IngestionResponse)
def ingest_webhook_event_alias(
    envelope: IngestionEnvelope,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    envelope.source_channel = "webhook"
    return ingest_event(db=db, current_user=current_user, envelope=envelope)


@router.post("/events/ingestion/polling", response_model=IngestionResponse)
def ingest_polling_event(
    envelope: IngestionEnvelope,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    envelope.source_channel = "polling"
    return ingest_event(db=db, current_user=current_user, envelope=envelope)


@router.post("/events/ingestion/tracking", response_model=IngestionResponse)
def ingest_tracking_event(
    envelope: IngestionEnvelope,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    envelope.source_channel = "tracking"
    return ingest_event(db=db, current_user=current_user, envelope=envelope)


@router.post("/events/ingestion/internal", response_model=IngestionResponse)
def ingest_internal_event(
    envelope: IngestionEnvelope,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    envelope.source_channel = "internal"
    return ingest_event(db=db, current_user=current_user, envelope=envelope)


@router.get("/events/store/customer/{customer_id}", response_model=list[EventRecordResponse])
def customer_events(
    customer_id: str,
    limit: int = Query(default=200, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tenant_id = require_tenant_id(current_user.tenant_id)
    return list_events_by_customer(db=db, tenant_id=tenant_id, customer_id=customer_id, limit=limit)


@router.get("/events/store/merchant/{merchant_id}", response_model=list[EventRecordResponse])
def merchant_events(
    merchant_id: int,
    limit: int = Query(default=200, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tenant_id = require_tenant_id(current_user.tenant_id)
    return list_events_by_merchant(db=db, tenant_id=tenant_id, merchant_id=merchant_id, limit=limit)


@router.get("/events/store/replay")
def replay_store_events(
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    merchant_id: int | None = None,
    customer_id: str | None = None,
    limit: int = Query(default=1000, ge=1, le=5000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tenant_id = require_tenant_id(current_user.tenant_id)
    return replay_events(
        db=db,
        tenant_id=tenant_id,
        start_at=start_at,
        end_at=end_at,
        merchant_id=merchant_id,
        customer_id=customer_id,
        limit=limit,
    )


@router.get("/integrations")
def list_integrations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tenant_id = require_tenant_id(current_user.tenant_id)
    return get_integrations_overview(db=db, tenant_id=tenant_id, merchant_id=current_user.id)


@router.post("/integrations/{connector_type}/connect")
def connect_data_integration(
    connector_type: str,
    payload: IntegrationConnectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tenant_id = require_tenant_id(current_user.tenant_id)
    return connect_integration(
        db=db,
        tenant_id=tenant_id,
        merchant_id=current_user.id,
        connector_type=connector_type,
        payload=payload,
    )
