from app.observability.correlation import CorrelationIdMiddleware
from app.observability.logging import RequestLoggingMiddleware, configure_json_logging
from app.observability.metrics import PrometheusMiddleware, mount_metrics_endpoint
from app.observability.tracing import configure_tracing, instrument_fastapi_app


def setup_fastapi_observability(app, service_name: str) -> None:
    configure_json_logging(service_name=service_name)
    configure_tracing(service_name=service_name)
    instrument_fastapi_app(app)

    # Middleware is executed in reverse add order.
    app.add_middleware(PrometheusMiddleware, service_name=service_name)
    app.add_middleware(RequestLoggingMiddleware, service_name=service_name)
    app.add_middleware(CorrelationIdMiddleware)
    mount_metrics_endpoint(app)

