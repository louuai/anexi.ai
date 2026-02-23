import os

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.celery import CeleryInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


_TRACING_CONFIGURED = False
_HTTPX_INSTRUMENTED = False
_REDIS_INSTRUMENTED = False
_CELERY_INSTRUMENTED = False


def _traces_endpoint() -> str:
    explicit = os.getenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", "").strip()
    if explicit:
        return explicit
    base = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://jaeger:4318").rstrip("/")
    return f"{base}/v1/traces"


def configure_tracing(service_name: str) -> None:
    global _TRACING_CONFIGURED
    if _TRACING_CONFIGURED:
        return

    if os.getenv("OBS_TRACING_ENABLED", "true").lower() in {"0", "false", "off"}:
        _TRACING_CONFIGURED = True
        return

    resource = Resource.create({"service.name": service_name})
    tracer_provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(
        endpoint=_traces_endpoint(),
        timeout=5,
    )
    tracer_provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(tracer_provider)
    _TRACING_CONFIGURED = True


def instrument_fastapi_app(app) -> None:
    FastAPIInstrumentor.instrument_app(app)
    instrument_http_clients()
    instrument_redis()


def instrument_http_clients() -> None:
    global _HTTPX_INSTRUMENTED
    if not _HTTPX_INSTRUMENTED:
        HTTPXClientInstrumentor().instrument()
        _HTTPX_INSTRUMENTED = True


def instrument_redis() -> None:
    global _REDIS_INSTRUMENTED
    if not _REDIS_INSTRUMENTED:
        RedisInstrumentor().instrument()
        _REDIS_INSTRUMENTED = True


def instrument_celery() -> None:
    global _CELERY_INSTRUMENTED
    if not _CELERY_INSTRUMENTED:
        CeleryInstrumentor().instrument()
        _CELERY_INSTRUMENTED = True

