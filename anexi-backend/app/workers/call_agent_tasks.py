from app.database import SessionLocal
from app.models import Order, Call, AIDecision
from app.workers.celery_app import celery_app


@celery_app.task(name="call_agent.run_for_order")
def run_call_agent_for_order(order_id: int, locale: str = "fr"):
    """
    Future-ready async call agent worker (current implementation is a simulation stub).
    """
    db = SessionLocal()
    try:
        order = db.get(Order, order_id)
        if not order:
            return {"ok": False, "reason": "order_not_found"}

        last_decision = (
            db.query(AIDecision)
            .filter(AIDecision.source_type == "order", AIDecision.source_id == order_id)
            .order_by(AIDecision.created_at.desc())
            .first()
        )
        ai_decision = "escalate"
        if last_decision and last_decision.decision == "auto_confirm":
            ai_decision = "confirm"
        elif last_decision and last_decision.decision == "reject":
            ai_decision = "reject"

        call = Call(
            order_id=order_id,
            agent_id=0,
            transcript=f"[{locale}] Simulated AI confirmation call for order #{order_id}",
            ai_score=last_decision.score if last_decision else None,
            ai_decision=ai_decision,
        )
        db.add(call)
        db.commit()
        db.refresh(call)
        return {"ok": True, "call_id": call.id, "order_id": order_id}
    finally:
        db.close()

