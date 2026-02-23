import os
from typing import Dict

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.observability import setup_fastapi_observability
from app.observability.context import (
    CORRELATION_ID_HEADER,
    REQUEST_ID_HEADER,
    get_correlation_id,
)

SERVICE_MAP: Dict[str, str] = {
    "auth": os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000"),
    "admin": os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000"),
    "orders": os.getenv("ORDERS_SERVICE_URL", "http://orders-service:8000"),
    "boutiques": os.getenv("ORDERS_SERVICE_URL", "http://orders-service:8000"),
    "ai": os.getenv("AI_SERVICE_URL", os.getenv("ANALYTICS_SERVICE_URL", "http://analytics-service:8000")),
    "payments": os.getenv("PAYMENTS_SERVICE_URL", "http://payments-service:8000"),
    "dashboard": os.getenv("ANALYTICS_SERVICE_URL", "http://analytics-service:8000"),
    "trust": os.getenv("TRUST_SERVICE_URL", "http://trust-service:8000"),
}

app = FastAPI(
    title="Anexi API Gateway",
    version="1.0.0",
    description="Gateway for Anexi microservices",
)
setup_fastapi_observability(app, service_name=os.getenv("OTEL_SERVICE_NAME", "api-gateway"))

REQUEST_TIMEOUT_SECONDS = float(os.getenv("GATEWAY_REQUEST_TIMEOUT_SECONDS", "15"))
HTTPX_LIMITS = httpx.Limits(max_keepalive_connections=50, max_connections=200)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_http_client: httpx.AsyncClient | None = None


@app.on_event("startup")
async def startup_event():
    global _http_client
    _http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(REQUEST_TIMEOUT_SECONDS),
        limits=HTTPX_LIMITS,
    )


@app.on_event("shutdown")
async def shutdown_event():
    global _http_client
    if _http_client is not None:
        await _http_client.aclose()
        _http_client = None


@app.get("/health")
def health():
    return {"status": "healthy", "service": "api-gateway"}


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
async def proxy(path: str, request: Request):
    raw_path = request.url.path
    stripped = raw_path.lstrip("/")
    if not stripped:
        return JSONResponse({"detail": "Unknown service route"}, status_code=404)

    prefix = stripped.split("/", 1)[0]
    service_url = SERVICE_MAP.get(prefix)
    if not service_url:
        return JSONResponse({"detail": "Unknown service route"}, status_code=404)

    target_url = f"{service_url}{raw_path}"
    if request.url.query:
        target_url = f"{target_url}?{request.url.query}"

    body = await request.body()
    headers = {k: v for k, v in request.headers.items() if k.lower() != "host"}
    correlation_id = get_correlation_id() or request.headers.get(CORRELATION_ID_HEADER, "")
    if correlation_id:
        headers[CORRELATION_ID_HEADER] = correlation_id
        headers[REQUEST_ID_HEADER] = correlation_id

    client = _http_client
    if client is None:
        return JSONResponse(
            {"detail": "Gateway HTTP client unavailable", "correlation_id": correlation_id},
            status_code=503,
            headers={
                CORRELATION_ID_HEADER: correlation_id,
                REQUEST_ID_HEADER: correlation_id,
            },
        )

    try:
        upstream = await client.request(
            method=request.method,
            url=target_url,
            headers=headers,
            content=body,
        )
    except httpx.TimeoutException:
        return JSONResponse(
            {"detail": f"Upstream timeout: {prefix}", "correlation_id": correlation_id},
            status_code=504,
            headers={
                CORRELATION_ID_HEADER: correlation_id,
                REQUEST_ID_HEADER: correlation_id,
            },
        )
    except httpx.RequestError:
        return JSONResponse(
            {"detail": f"Upstream unavailable: {prefix}", "correlation_id": correlation_id},
            status_code=503,
            headers={
                CORRELATION_ID_HEADER: correlation_id,
                REQUEST_ID_HEADER: correlation_id,
            },
        )

    response_headers = {k: v for k, v in upstream.headers.items() if k.lower() not in {"content-encoding", "transfer-encoding", "connection"}}
    if correlation_id:
        response_headers[CORRELATION_ID_HEADER] = correlation_id
        response_headers[REQUEST_ID_HEADER] = correlation_id
    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=response_headers,
        media_type=upstream.headers.get("content-type"),
    )
