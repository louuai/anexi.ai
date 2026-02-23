import json
import logging
import os
import sys
from datetime import datetime, timezone

from opentelemetry import trace
from starlette.middleware.base import BaseHTTPMiddleware

from app.observability.context import get_correlation_id


class JsonLogFormatter(logging.Formatter):
    def __init__(self, service_name: str):
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        now = datetime.now(timezone.utc).isoformat()
        span = trace.get_current_span()
        span_ctx = span.get_span_context() if span else None

        payload: dict[str, object] = {
            "timestamp": now,
            "level": record.levelname,
            "logger": record.name,
            "service": self.service_name,
            "message": record.getMessage(),
            "correlation_id": get_correlation_id() or None,
        }

        if span_ctx and span_ctx.is_valid:
            payload["trace_id"] = f"{span_ctx.trace_id:032x}"
            payload["span_id"] = f"{span_ctx.span_id:016x}"

        for key in ("method", "path", "status_code", "duration_ms", "client_ip"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=True)


def configure_json_logging(service_name: str) -> None:
    root_logger = logging.getLogger()
    if getattr(root_logger, "_anexi_json_logging", False):
        return

    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonLogFormatter(service_name=service_name))

    root_logger.handlers = [handler]
    root_logger.setLevel(level)
    root_logger._anexi_json_logging = True  # type: ignore[attr-defined]

    # Keep noisy libraries under control.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, service_name: str):
        super().__init__(app)
        self.service_name = service_name
        self.logger = logging.getLogger("http.request")

    async def dispatch(self, request, call_next):
        import time

        started = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        self.logger.info(
            "request_completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "client_ip": request.client.host if request.client else "",
            },
        )
        return response

