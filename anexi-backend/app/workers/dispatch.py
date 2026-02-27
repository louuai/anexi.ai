import logging

from app.observability.context import CORRELATION_ID_HEADER, get_correlation_id


logger = logging.getLogger(__name__)


def enqueue_task(task, *args, **kwargs):
    """
    Fire-and-forget task dispatch with safe fallback if broker is unavailable.
    """
    try:
        correlation_id = get_correlation_id()
        headers = {CORRELATION_ID_HEADER: correlation_id} if correlation_id else None
        task.apply_async(args=args, kwargs=kwargs, headers=headers)
        return True
    except Exception:
        logger.exception("Failed to enqueue task %s", getattr(task, "name", str(task)))
        return False


def enqueue_task_result(task, *args, **kwargs):
    """
    Dispatch task and return AsyncResult so caller can track progress.
    """
    try:
        correlation_id = get_correlation_id()
        headers = {CORRELATION_ID_HEADER: correlation_id} if correlation_id else None
        return task.apply_async(args=args, kwargs=kwargs, headers=headers)
    except Exception:
        logger.exception("Failed to enqueue task %s", getattr(task, "name", str(task)))
        return None
