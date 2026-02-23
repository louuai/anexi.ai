import os

from celery import Celery

from app.workers.observability import setup_worker_observability


CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

celery_app = Celery(
    "anexi_workers",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=[
        "app.workers.decision_tasks",
        "app.workers.analytics_tasks",
        "app.workers.payment_tasks",
        "app.workers.call_agent_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_send_task_events=True,
    task_send_sent_event=True,
)

setup_worker_observability(service_name=os.getenv("OTEL_SERVICE_NAME", "celery-worker"))
