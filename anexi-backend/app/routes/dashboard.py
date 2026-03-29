from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Order, Boutique, Customer, AIDecision
from app.modules.events.models import CustomerState, EventRecord, MerchantIntegration
from app.routes.auth import get_current_user
from app.utils.tenant import require_tenant_id

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def _get_user_boutique_ids(db: Session, current_user: User, boutique_id: int | None) -> list[int]:
    tenant_id = require_tenant_id(current_user.tenant_id)
    if boutique_id:
        boutique = (
            db.query(Boutique)
            .filter(
                Boutique.id == boutique_id,
                Boutique.owner_id == current_user.id,
                Boutique.tenant_id == tenant_id,
            )
            .first()
        )
        return [boutique.id] if boutique else []

    return [
        b_id
        for (b_id,) in db.query(Boutique.id)
        .filter(Boutique.owner_id == current_user.id, Boutique.tenant_id == tenant_id)
        .all()
    ]


@router.get("/stats")
def get_dashboard_stats(
    boutique_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tenant_id = require_tenant_id(current_user.tenant_id)
    boutique_ids = _get_user_boutique_ids(db, current_user, boutique_id)
    if not boutique_ids:
        return {
            "total_orders": 0,
            "pending_orders": 0,
            "confirmed_orders": 0,
            "rejected_orders": 0,
            "total_revenue": 0,
            "total_customers": 0,
            "orders_today": 0,
            "high_risk_orders": 0,
        }

    total_orders = (
        db.query(func.count(Order.id))
        .filter(Order.tenant_id == tenant_id, Order.boutique_id.in_(boutique_ids))
        .scalar()
    )
    pending_orders = (
        db.query(func.count(Order.id))
        .filter(Order.tenant_id == tenant_id, Order.boutique_id.in_(boutique_ids), Order.status == "pending")
        .scalar()
    )
    confirmed_orders = (
        db.query(func.count(Order.id))
        .filter(Order.tenant_id == tenant_id, Order.boutique_id.in_(boutique_ids), Order.status == "confirmed")
        .scalar()
    )
    rejected_orders = (
        db.query(func.count(Order.id))
        .filter(Order.tenant_id == tenant_id, Order.boutique_id.in_(boutique_ids), Order.status == "rejected")
        .scalar()
    )
    total_revenue = (
        db.query(func.sum(Order.price))
        .filter(Order.tenant_id == tenant_id, Order.boutique_id.in_(boutique_ids), Order.status == "confirmed")
        .scalar()
        or 0
    )
    total_customers = (
        db.query(func.count(Customer.id))
        .filter(Customer.tenant_id == tenant_id, Customer.boutique_id.in_(boutique_ids))
        .scalar()
    )
    today = datetime.utcnow().date()
    orders_today = (
        db.query(func.count(Order.id))
        .filter(
            Order.tenant_id == tenant_id,
            Order.boutique_id.in_(boutique_ids),
            func.date(Order.created_at) == today,
        )
        .scalar()
    )
    high_risk_orders = (
        db.query(func.count(AIDecision.id))
        .filter(
            AIDecision.tenant_id == tenant_id,
            AIDecision.decision == "reject",
            AIDecision.created_at >= datetime.utcnow() - timedelta(days=7),
        )
        .scalar()
    )

    return {
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "confirmed_orders": confirmed_orders,
        "rejected_orders": rejected_orders,
        "total_revenue": float(total_revenue),
        "total_customers": total_customers,
        "orders_today": orders_today,
        "high_risk_orders": high_risk_orders,
    }


@router.get("/recent-orders")
def get_recent_orders(
    limit: int = 10,
    boutique_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tenant_id = require_tenant_id(current_user.tenant_id)
    boutique_ids = _get_user_boutique_ids(db, current_user, boutique_id)
    if not boutique_ids:
        return []

    orders = (
        db.query(Order)
        .filter(Order.tenant_id == tenant_id, Order.boutique_id.in_(boutique_ids))
        .order_by(Order.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": o.id,
            "product_name": o.product_name,
            "price": float(o.price),
            "status": o.status,
            "created_at": o.created_at,
            "customer_id": o.customer_id,
        }
        for o in orders
    ]


@router.get("/revenue-chart")
def get_revenue_chart(
    days: int = 7,
    boutique_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tenant_id = require_tenant_id(current_user.tenant_id)
    boutique_ids = _get_user_boutique_ids(db, current_user, boutique_id)
    if not boutique_ids:
        return {"labels": [], "data": []}

    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days - 1)

    revenue_data = []
    labels = []
    current_date = start_date
    while current_date <= end_date:
        daily_revenue = (
            db.query(func.sum(Order.price))
            .filter(
                Order.tenant_id == tenant_id,
                Order.boutique_id.in_(boutique_ids),
                Order.status == "confirmed",
                func.date(Order.created_at) == current_date,
            )
            .scalar()
            or 0
        )
        revenue_data.append(float(daily_revenue))
        labels.append(current_date.strftime("%Y-%m-%d"))
        current_date += timedelta(days=1)

    return {"labels": labels, "data": revenue_data}


@router.get("/event-intelligence")
def get_event_intelligence(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tenant_id = require_tenant_id(current_user.tenant_id)
    merchant_id = current_user.id
    now = datetime.utcnow()
    today = now.date()
    last_24h = now - timedelta(hours=24)

    events_today = (
        db.query(func.count(EventRecord.id))
        .filter(
            EventRecord.tenant_id == tenant_id,
            EventRecord.merchant_id == merchant_id,
            func.date(EventRecord.timestamp) == today,
        )
        .scalar()
        or 0
    )
    events_last_24h = (
        db.query(func.count(EventRecord.id))
        .filter(
            EventRecord.tenant_id == tenant_id,
            EventRecord.merchant_id == merchant_id,
            EventRecord.timestamp >= last_24h,
        )
        .scalar()
        or 0
    )

    by_source_rows = (
        db.query(EventRecord.source_channel, func.count(EventRecord.id))
        .filter(EventRecord.tenant_id == tenant_id, EventRecord.merchant_id == merchant_id)
        .group_by(EventRecord.source_channel)
        .all()
    )
    events_by_source = {str(source): int(total) for source, total in by_source_rows}

    snapshots = (
        db.query(CustomerState)
        .filter(
            CustomerState.tenant_id == tenant_id,
            CustomerState.merchant_id == merchant_id,
        )
        .all()
    )
    total_customers = len(snapshots)
    high_trust_customers = sum(1 for row in snapshots if float(row.trust_score or 0.0) >= 75.0)
    low_trust_customers = sum(1 for row in snapshots if float(row.trust_score or 0.0) < 40.0)
    fraud_risk_customers = sum(1 for row in snapshots if float(row.trust_score or 0.0) < 25.0)

    def _serialize(rows: list[EventRecord]) -> list[dict]:
        return [
            {
                "event_type": row.event_type,
                "customer_id": row.customer_id,
                "source": row.source_platform,
                "timestamp": row.timestamp,
            }
            for row in rows
        ]

    latest_events = (
        db.query(EventRecord)
        .filter(EventRecord.tenant_id == tenant_id, EventRecord.merchant_id == merchant_id)
        .order_by(EventRecord.timestamp.desc(), EventRecord.id.desc())
        .limit(10)
        .all()
    )
    latest_purchases = (
        db.query(EventRecord)
        .filter(
            EventRecord.tenant_id == tenant_id,
            EventRecord.merchant_id == merchant_id,
            EventRecord.event_type == "customer_purchase",
        )
        .order_by(EventRecord.timestamp.desc(), EventRecord.id.desc())
        .limit(10)
        .all()
    )
    latest_cancellations = (
        db.query(EventRecord)
        .filter(
            EventRecord.tenant_id == tenant_id,
            EventRecord.merchant_id == merchant_id,
            EventRecord.event_type.in_(("order_cancelled", "order_refunded")),
        )
        .order_by(EventRecord.timestamp.desc(), EventRecord.id.desc())
        .limit(10)
        .all()
    )

    integrations = (
        db.query(MerchantIntegration)
        .filter(MerchantIntegration.tenant_id == tenant_id, MerchantIntegration.merchant_id == merchant_id)
        .all()
    )
    integration_map = {row.connector_type: row for row in integrations}
    integration_status = {
        "shopify_connected": bool(integration_map.get("shopify") and integration_map["shopify"].status == "connected"),
        "webhook_active": bool(integration_map.get("webhook") and integration_map["webhook"].status == "connected"),
        "pixel_active": bool(
            integration_map.get("tracking_script") and integration_map["tracking_script"].status == "connected"
        ),
    }

    return {
        "event_activity": {
            "events_today": int(events_today),
            "events_last_24h": int(events_last_24h),
            "events_by_source": events_by_source,
        },
        "customer_intelligence": {
            "total_customers": total_customers,
            "high_trust_customers": high_trust_customers,
            "low_trust_customers": low_trust_customers,
            "fraud_risk_customers": fraud_risk_customers,
        },
        "timeline_activity": {
            "latest_events": _serialize(latest_events),
            "latest_purchases": _serialize(latest_purchases),
            "latest_cancellations": _serialize(latest_cancellations),
        },
        "integration_status": integration_status,
    }


@router.get("/live-event-feed")
def get_live_event_feed(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tenant_id = require_tenant_id(current_user.tenant_id)
    merchant_id = current_user.id
    rows = (
        db.query(EventRecord)
        .filter(EventRecord.tenant_id == tenant_id, EventRecord.merchant_id == merchant_id)
        .order_by(EventRecord.timestamp.desc(), EventRecord.id.desc())
        .limit(max(1, min(limit, 200)))
        .all()
    )
    return [
        {
            "event_type": row.event_type,
            "customer_id": row.customer_id,
            "source": row.source_platform,
            "timestamp": row.timestamp,
        }
        for row in rows
    ]
