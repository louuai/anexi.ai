import os
import threading
import time

import redis
from celery.signals import task_failure, task_postrun, task_prerun, worker_ready
from prometheus_client import Counter, Gauge, Histogram, start_http_server

from app.observability.context import get_correlation_id
from app.observability.context import CORRELATION_ID_HEADER, set_correlation_id
from app.observability.logging import configure_json_logging
from app.observability.tracing import configure_tracing, instrument_celery, instrument_redis


CELERY_TASKS_TOTAL = Counter(
    "anexi_celery_tasks_total",
    "Total Celery tasks by status",
    ["service", "task_name", "status"],
)
CELERY_TASK_DURATION_SECONDS = Histogram(
    "anexi_celery_task_duration_seconds",
    "Celery task execution duration",
    ["service", "task_name"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10, 30, 60),
)
CELERY_QUEUE_LENGTH = Gauge(
    "anexi_celery_queue_length",
    "Current Redis queue length",
    ["service", "queue_name"],
)
CELERY_WORKER_UP = Gauge("anexi_celery_worker_up", "Worker liveness", ["service"])

_OBS_INITIALIZED = False
_QUEUE_THREAD_STARTED = False
_task_start_times: dict[str, float] = {}


def _queues_from_env() -> list[str]:
    raw = os.getenv("CELERY_METRICS_QUEUES", "celery")
    return [q.strip() for q in raw.split(",") if q.strip()]


def _start_queue_polling(service_name: str) -> None:
    global _QUEUE_THREAD_STARTED
    if _QUEUE_THREAD_STARTED:
        return
    _QUEUE_THREAD_STARTED = True

    interval = float(os.getenv("CELERY_QUEUE_POLL_INTERVAL_SECONDS", "10"))
    queues = _queues_from_env()
    broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    client = redis.Redis.from_url(broker_url)

    def poller():
        while True:
            for queue in queues:
                try:
                    size = int(client.llen(queue))
                except Exception:
                    size = -1
                CELERY_QUEUE_LENGTH.labels(service=service_name, queue_name=queue).set(size)
            time.sleep(interval)

    threading.Thread(target=poller, daemon=True, name="celery-queue-metrics").start()


def _task_key(task_id: str, task_name: str) -> str:
    return f"{task_id}:{task_name}"


def setup_worker_observability(service_name: str = "celery-worker") -> None:
    global _OBS_INITIALIZED
    if _OBS_INITIALIZED:
        return

    configure_json_logging(service_name=service_name)
    configure_tracing(service_name=service_name)
    instrument_celery()
    instrument_redis()

    metrics_port = int(os.getenv("WORKER_METRICS_PORT", "9100"))
    start_http_server(metrics_port)
    CELERY_WORKER_UP.labels(service=service_name).set(1)

    @task_prerun.connect(weak=False)
    def on_task_prerun(task_id=None, task=None, **_kwargs):
        name = getattr(task, "name", "unknown_task")
        headers = getattr(getattr(task, "request", None), "headers", {}) or {}
        correlation_id = headers.get(CORRELATION_ID_HEADER, "")
        if correlation_id:
            set_correlation_id(str(correlation_id))
        CELERY_TASKS_TOTAL.labels(service=service_name, task_name=name, status="started").inc()
        _task_start_times[_task_key(task_id or "", name)] = time.perf_counter()

    @task_postrun.connect(weak=False)
    def on_task_postrun(task_id=None, task=None, state=None, **_kwargs):
        name = getattr(task, "name", "unknown_task")
        key = _task_key(task_id or "", name)
        started = _task_start_times.pop(key, None)
        if started is not None:
            duration = time.perf_counter() - started
            CELERY_TASK_DURATION_SECONDS.labels(service=service_name, task_name=name).observe(duration)
        status = (state or "unknown").lower()
        CELERY_TASKS_TOTAL.labels(service=service_name, task_name=name, status=status).inc()
        set_correlation_id("")

    @task_failure.connect(weak=False)
    def on_task_failure(task_id=None, exception=None, traceback=None, sender=None, **_kwargs):
        del traceback
        name = getattr(sender, "name", "unknown_task")
        CELERY_TASKS_TOTAL.labels(service=service_name, task_name=name, status="failed").inc()
        import logging

        logger = logging.getLogger("celery.task")
        logger.exception(
            "task_failed",
            extra={
                "task_name": name,
                "task_id": task_id,
                "error": str(exception),
                "correlation_id": get_correlation_id() or None,
            },
        )

    @worker_ready.connect(weak=False)
    def on_worker_ready(**_kwargs):
        _start_queue_polling(service_name=service_name)

    _OBS_INITIALIZED = True
