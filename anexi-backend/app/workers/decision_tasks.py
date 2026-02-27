from decimal import Decimal

from app.database import SessionLocal
from app.models import Order, AIDecision
from app.workers.celery_app import celery_app
from app.workers.dispatch import enqueue_task
from app.workers.call_agent_tasks import run_call_agent_for_order


@celery_app.task(name="decision.process_order_decision")
def process_order_decision(order_id: int):
    """
    Behavioral Brain async scoring for a new/updated order.
    """
    db = SessionLocal()
    try:
        order = db.get(Order, order_id)
        if not order:
            return {"ok": False, "reason": "order_not_found"}
        tenant_id = int(order.tenant_id or 0)
        if tenant_id <= 0:
            return {"ok": False, "reason": "tenant_missing"}

        customer_orders = (
            db.query(Order)
            .filter(Order.customer_id == order.customer_id, Order.tenant_id == tenant_id)
            .all()
        )
        total_orders = len(customer_orders)
        confirmed_orders = sum(1 for o in customer_orders if o.status == "confirmed")
        cancellation_orders = sum(1 for o in customer_orders if o.status in ("rejected", "cancelled"))

        if total_orders == 0:
            trust_score = Decimal("50.00")
        else:
            confirmation_rate = Decimal(confirmed_orders) / Decimal(total_orders)
            cancel_rate = Decimal(cancellation_orders) / Decimal(total_orders)
            score = Decimal("40.00") + (confirmation_rate * Decimal("70.00")) - (cancel_rate * Decimal("30.00"))
            trust_score = max(Decimal("0.00"), min(Decimal("100.00"), score.quantize(Decimal("0.01"))))

        if trust_score >= Decimal("75.00"):
            decision = "auto_confirm"
        elif trust_score < Decimal("40.00"):
            decision = "reject"
        else:
            decision = "call_required"

        db.add(
            AIDecision(
                tenant_id=tenant_id,
                source_type="order",
                source_id=order.id,
                score=trust_score,
                decision=decision,
                explanation=f"score={trust_score}, total_orders={total_orders}, confirmed={confirmed_orders}",
            )
        )
        db.commit()

        if decision == "call_required":
            enqueue_task(run_call_agent_for_order, order.id, "fr")

        return {"ok": True, "order_id": order.id, "score": str(trust_score), "decision": decision}
    finally:
        db.close()
