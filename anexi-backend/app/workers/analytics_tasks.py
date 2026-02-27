from sqlalchemy import func

from app.database import SessionLocal
from app.models import Order, Payment, Boutique, User
from app.workers.celery_app import celery_app


@celery_app.task(name="analytics.refresh_for_user")
def refresh_analytics_for_user(user_id: int, reason: str = "manual"):
    """
    Async analytics aggregation (extensible for materialized caches).
    """
    db = SessionLocal()
    try:
        user = db.get(User, user_id)
        if not user or not user.tenant_id:
            return {"ok": False, "user_id": user_id, "reason": "user_or_tenant_missing"}
        tenant_id = int(user.tenant_id)

        boutique_ids = [
            row[0]
            for row in db.query(Boutique.id)
            .filter(Boutique.owner_id == user_id, Boutique.tenant_id == tenant_id)
            .all()
        ]
        if not boutique_ids:
            return {"ok": True, "user_id": user_id, "reason": reason, "orders": 0, "revenue": 0}

        total_orders = (
            db.query(func.count(Order.id))
            .filter(Order.boutique_id.in_(boutique_ids), Order.tenant_id == tenant_id)
            .scalar()
            or 0
        )
        total_revenue = (
            db.query(func.coalesce(func.sum(Payment.amount), 0))
            .filter(Payment.user_id == user_id, Payment.tenant_id == tenant_id)
            .scalar()
            or 0
        )
        return {
            "ok": True,
            "user_id": user_id,
            "reason": reason,
            "orders": int(total_orders),
            "revenue": float(total_revenue),
        }
    finally:
        db.close()
