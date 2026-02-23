from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


HTTP_REQUESTS_TOTAL = Counter(
    "anexi_http_requests_total",
    "Total HTTP requests",
    ["service", "method", "path", "status_code"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "anexi_http_request_duration_seconds",
    "HTTP request duration",
    ["service", "method", "path"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10),
)

HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "anexi_http_requests_in_progress",
    "In-progress HTTP requests",
    ["service", "method", "path"],
)


def _route_path(request) -> str:
    route = request.scope.get("route")
    route_path = getattr(route, "path", None)
    return route_path or request.url.path


class PrometheusMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, service_name: str):
        super().__init__(app)
        self.service_name = service_name

    async def dispatch(self, request, call_next):
        import time

        path = _route_path(request)
        method = request.method
        in_progress = HTTP_REQUESTS_IN_PROGRESS.labels(
            service=self.service_name,
            method=method,
            path=path,
        )
        in_progress.inc()
        started = time.perf_counter()
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception:
            status_code = 500
            raise
        finally:
            duration = time.perf_counter() - started
            HTTP_REQUEST_DURATION_SECONDS.labels(
                service=self.service_name,
                method=method,
                path=path,
            ).observe(duration)
            HTTP_REQUESTS_TOTAL.labels(
                service=self.service_name,
                method=method,
                path=path,
                status_code=str(status_code),
            ).inc()
            in_progress.dec()
        return response


def mount_metrics_endpoint(app) -> None:
    @app.get("/metrics", include_in_schema=False)
    def metrics():
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

