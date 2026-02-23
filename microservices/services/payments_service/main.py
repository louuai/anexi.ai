import os

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.observability import setup_fastapi_observability
from app.observability.context import CORRELATION_ID_HEADER, REQUEST_ID_HEADER, get_correlation_id
from app.routes import payments


ANALYTICS_INTERNAL_URL = os.getenv("ANALYTICS_INTERNAL_URL", "http://analytics-service:8000/internal/events")

app = FastAPI(
    title="Anexi Payments Service",
    version="1.0.0",
    description="Payments and webhook processing service",
)
setup_fastapi_observability(app, service_name=os.getenv("OTEL_SERVICE_NAME", "payments-service"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(payments.router)


@app.post("/internal/analytics/emit")
async def emit_analytics_event(payload: dict, request: Request):
    """
    Example API-based service-to-service communication.
    Used when another service wants an explicit sync call instead of queue dispatch.
    """
    correlation_id = get_correlation_id() or request.headers.get(CORRELATION_ID_HEADER, "")
    headers = {}
    if correlation_id:
        headers[CORRELATION_ID_HEADER] = correlation_id
        headers[REQUEST_ID_HEADER] = correlation_id

    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            response = await client.post(
                ANALYTICS_INTERNAL_URL,
                json=payload or {},
                headers=headers,
            )
            return {"ok": response.is_success, "status_code": response.status_code}
        except Exception:
            return {"ok": False, "status_code": 0}


@app.get("/health")
def health():
    return {"status": "healthy", "service": "payments-service"}
