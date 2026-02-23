import os

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import get_db
from app.observability import setup_fastapi_observability
from app.routes import dashboard
from app.workers.dispatch import enqueue_task
from app.workers.analytics_tasks import refresh_analytics_for_user


app = FastAPI(
    title="Anexi Analytics Service",
    version="1.0.0",
    description="Dashboard and analytics domain service",
)
setup_fastapi_observability(app, service_name=os.getenv("OTEL_SERVICE_NAME", "ai-service"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router)


@app.post("/internal/events")
def receive_internal_event(event: dict, db: Session = Depends(get_db)):
    """
    Internal orchestration endpoint used by other services to trigger async recompute.
    """
    del db
    user_id = (event or {}).get("user_id")
    reason = (event or {}).get("reason", "internal_event")
    accepted = False
    if user_id:
        accepted = enqueue_task(refresh_analytics_for_user, int(user_id), str(reason))
    return {"accepted": bool(accepted), "event": event or {}}


@app.get("/health")
def health():
    return {"status": "healthy", "service": "analytics-service"}
