from datetime import datetime

from sqlalchemy.orm import Session

from app.modules.events.models import CustomerState, EventRecord, MerchantIntegration
from app.modules.events.schemas import StandardEvent


class EventStoreRepository:
    def __init__(self, db: Session):
        self.db = db

    def append(self, source_channel: str, event: StandardEvent) -> EventRecord:
        row = EventRecord(
            event_id=event.event_id,
            tenant_id=event.tenant_id,
            merchant_id=event.merchant_id,
            customer_id=event.customer_id,
            event_type=event.event_type,
            event_payload=event.event_payload,
            source_platform=event.source_platform,
            source_channel=source_channel,
            timestamp=event.timestamp,
            correlation_id=event.correlation_id,
            trace_id=event.trace_id,
        )
        self.db.add(row)
        self._upsert_customer_state(event)
        self._touch_integration(event=event, source_channel=source_channel)
        self.db.commit()
        self.db.refresh(row)
        return row

    def _upsert_customer_state(self, event: StandardEvent) -> None:
        state = (
            self.db.query(CustomerState)
            .filter(
                CustomerState.tenant_id == event.tenant_id,
                CustomerState.merchant_id == event.merchant_id,
                CustomerState.customer_id == event.customer_id,
            )
            .first()
        )
        if state is None:
            state = CustomerState(
                tenant_id=event.tenant_id,
                merchant_id=event.merchant_id,
                customer_id=event.customer_id,
                total_orders=0,
                total_refunds=0,
                trust_score=50.0,
                last_event=event.event_type,
                last_event_at=event.timestamp,
                updated_at=datetime.utcnow(),
            )
            self.db.add(state)

        if event.event_type == "customer_purchase":
            state.total_orders += 1
            state.trust_score = min(100.0, float(state.trust_score) + 5.0)
        elif event.event_type in {"order_refunded", "order_cancelled"}:
            state.total_refunds += 1
            state.trust_score = max(0.0, float(state.trust_score) - 8.0)
        elif event.event_type == "call_confirmed":
            state.trust_score = min(100.0, float(state.trust_score) + 3.0)
        elif event.event_type == "call_failed":
            state.trust_score = max(0.0, float(state.trust_score) - 4.0)

        state.last_event = event.event_type
        state.last_event_at = event.timestamp
        state.updated_at = datetime.utcnow()

    def _touch_integration(self, event: StandardEvent, source_channel: str) -> None:
        connector_type = None
        source_platform = str(event.source_platform or "").strip().lower()
        if source_platform == "shopify":
            connector_type = "shopify"
        elif source_platform == "woocommerce":
            connector_type = "woocommerce"
        elif source_channel == "tracking":
            connector_type = "tracking_script"
        elif source_channel == "webhook":
            connector_type = "webhook"
        elif source_channel == "polling":
            connector_type = "api"

        if connector_type is None:
            return

        row = (
            self.db.query(MerchantIntegration)
            .filter(
                MerchantIntegration.tenant_id == event.tenant_id,
                MerchantIntegration.merchant_id == event.merchant_id,
                MerchantIntegration.connector_type == connector_type,
            )
            .first()
        )
        if row is None:
            row = MerchantIntegration(
                tenant_id=event.tenant_id,
                merchant_id=event.merchant_id,
                connector_type=connector_type,
                status="connected",
                connected_at=datetime.utcnow(),
                events_received=0,
                config={},
            )
            self.db.add(row)

        row.status = "connected"
        row.last_event_at = event.timestamp
        row.events_received = int(row.events_received or 0) + 1
        row.updated_at = datetime.utcnow()

    def by_customer(
        self,
        tenant_id: int,
        customer_id: str,
        limit: int = 200,
    ) -> list[EventRecord]:
        return (
            self.db.query(EventRecord)
            .filter(
                EventRecord.tenant_id == tenant_id,
                EventRecord.customer_id == customer_id,
            )
            .order_by(EventRecord.timestamp.asc(), EventRecord.id.asc())
            .limit(limit)
            .all()
        )

    def by_merchant(
        self,
        tenant_id: int,
        merchant_id: int,
        limit: int = 200,
    ) -> list[EventRecord]:
        return (
            self.db.query(EventRecord)
            .filter(
                EventRecord.tenant_id == tenant_id,
                EventRecord.merchant_id == merchant_id,
            )
            .order_by(EventRecord.timestamp.desc(), EventRecord.id.desc())
            .limit(limit)
            .all()
        )

    def replay(
        self,
        tenant_id: int,
        start_at: datetime,
        end_at: datetime,
        merchant_id: int | None = None,
        customer_id: str | None = None,
        limit: int = 1000,
    ) -> list[EventRecord]:
        query = self.db.query(EventRecord).filter(
            EventRecord.tenant_id == tenant_id,
            EventRecord.timestamp >= start_at,
            EventRecord.timestamp <= end_at,
        )
        if merchant_id is not None:
            query = query.filter(EventRecord.merchant_id == merchant_id)
        if customer_id is not None:
            query = query.filter(EventRecord.customer_id == customer_id)
        return (
            query.order_by(EventRecord.timestamp.asc(), EventRecord.id.asc())
            .limit(limit)
            .all()
        )

    def list_customer_states(self, tenant_id: int, merchant_id: int) -> list[CustomerState]:
        return (
            self.db.query(CustomerState)
            .filter(
                CustomerState.tenant_id == tenant_id,
                CustomerState.merchant_id == merchant_id,
            )
            .all()
        )

    def latest_events(self, tenant_id: int, merchant_id: int, limit: int = 20) -> list[EventRecord]:
        return (
            self.db.query(EventRecord)
            .filter(
                EventRecord.tenant_id == tenant_id,
                EventRecord.merchant_id == merchant_id,
            )
            .order_by(EventRecord.timestamp.desc(), EventRecord.id.desc())
            .limit(limit)
            .all()
        )

    def upsert_merchant_integration(
        self,
        tenant_id: int,
        merchant_id: int,
        connector_type: str,
        status: str,
        config: dict,
        webhook_secret: str | None = None,
    ) -> MerchantIntegration:
        row = (
            self.db.query(MerchantIntegration)
            .filter(
                MerchantIntegration.tenant_id == tenant_id,
                MerchantIntegration.merchant_id == merchant_id,
                MerchantIntegration.connector_type == connector_type,
            )
            .first()
        )
        now = datetime.utcnow()
        if row is None:
            row = MerchantIntegration(
                tenant_id=tenant_id,
                merchant_id=merchant_id,
                connector_type=connector_type,
                status=status,
                connected_at=now if status == "connected" else None,
                config=config or {},
                webhook_secret=webhook_secret,
                events_received=0,
            )
            self.db.add(row)
        else:
            row.status = status
            if status == "connected" and row.connected_at is None:
                row.connected_at = now
            row.config = config or row.config or {}
            if webhook_secret is not None:
                row.webhook_secret = webhook_secret
            row.updated_at = now

        self.db.commit()
        self.db.refresh(row)
        return row

    def list_merchant_integrations(self, tenant_id: int, merchant_id: int) -> list[MerchantIntegration]:
        return (
            self.db.query(MerchantIntegration)
            .filter(
                MerchantIntegration.tenant_id == tenant_id,
                MerchantIntegration.merchant_id == merchant_id,
            )
            .all()
        )
