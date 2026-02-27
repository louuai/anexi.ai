from app.database import SessionLocal
from app.modules.trust.schemas import TrustEvaluateRequest
from app.modules.trust.service import evaluate_interaction
from app.workers.celery_app import celery_app


@celery_app.task(name="trust.evaluate_interaction")
def evaluate_trust_interaction_task(tenant_id: int, payload: dict):
    """
    Async Trust evaluation task (Redis/Celery-backed).
    """
    db = SessionLocal()
    try:
        parsed = TrustEvaluateRequest(**(payload or {}))
        result = evaluate_interaction(db=db, tenant_id=int(tenant_id), payload=parsed)
        return {"ok": True, "interaction": result.model_dump(mode="json")}
    finally:
        db.close()

