from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Order, Boutique, Customer, AIDecision
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
