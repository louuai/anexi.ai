from typing import Any, Dict

from app.workers.celery_app import celery_app
from app.workers.dispatch import enqueue_task
from app.workers.analytics_tasks import refresh_analytics_for_user


@celery_app.task(name="payments.process_webhook")
def process_payment_webhook_event(event: Dict[str, Any]):
    """
    Async payment webhook processor.
    """
    event_type = (event or {}).get("type", "unknown")
    data = (event or {}).get("data", {}) or {}
    user_id = data.get("user_id")

    if user_id:
        enqueue_task(refresh_analytics_for_user, int(user_id), f"payment_webhook:{event_type}")

    return {"ok": True, "event_type": event_type}

