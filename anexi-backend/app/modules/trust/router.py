from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from celery.result import AsyncResult

from app.database import get_db
from app.models import User
from app.modules.trust.schemas import (
    TrustEvaluateRequest,
    TrustInteractionsPage,
    TrustInteractionResponse,
    TrustMetricsSummary,
    TrustMetricsTimeline,
)
from app.modules.trust.service import evaluate_interaction, get_interactions, get_metrics_summary, get_metrics_timeline
from app.routes.auth import get_current_user
from app.utils.tenant import require_tenant_id
from app.workers.celery_app import celery_app
from app.workers.dispatch import enqueue_task_result
from app.workers.trust_tasks import evaluate_trust_interaction_task

router = APIRouter(tags=["Trust"])


@router.post("/internal/trust/evaluate", response_model=TrustInteractionResponse)
def evaluate_interaction_endpoint(
    payload: TrustEvaluateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tenant_id = require_tenant_id(current_user.tenant_id)
    return evaluate_interaction(db=db, tenant_id=tenant_id, payload=payload)


@router.post("/internal/trust/evaluate/async", response_model=dict, status_code=202)
def evaluate_interaction_async_endpoint(
    payload: TrustEvaluateRequest,
    current_user: User = Depends(get_current_user),
):
    tenant_id = require_tenant_id(current_user.tenant_id)
    task = enqueue_task_result(
        evaluate_trust_interaction_task,
        tenant_id,
        payload.model_dump(mode="json"),
    )
    if task is None:
        return {"queued": False, "detail": "Unable to enqueue trust evaluation"}
    return {"queued": True, "task_id": task.id, "state": "PENDING"}


@router.get("/internal/trust/tasks/{task_id}", response_model=dict)
def get_trust_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
):
    # Ensure caller is authenticated and has tenant context.
    require_tenant_id(current_user.tenant_id)
    result = AsyncResult(task_id, app=celery_app)
    payload = {
        "task_id": task_id,
        "state": result.state,
    }
    if result.state == "SUCCESS":
        payload["result"] = result.result
    elif result.state == "FAILURE":
        payload["error"] = str(result.result)
    return payload


@router.get("/trust/interactions", response_model=TrustInteractionsPage)
def list_interactions_endpoint(
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    campaign_id: str | None = None,
    segment: str | None = None,
    score_min: float | None = Query(default=None, ge=0, le=100),
    score_max: float | None = Query(default=None, ge=0, le=100),
    sort: str = Query(default="date_desc", pattern="^(date_desc|date_asc|score_desc|score_asc)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tenant_id = require_tenant_id(current_user.tenant_id)
    return get_interactions(
        db=db,
        tenant_id=tenant_id,
        limit=limit,
        offset=offset,
        campaign_id=campaign_id,
        segment=segment,
        score_min=score_min,
        score_max=score_max,
        sort=sort,
    )


@router.get("/trust/metrics/summary", response_model=TrustMetricsSummary)
def summary_metrics_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tenant_id = require_tenant_id(current_user.tenant_id)
    return get_metrics_summary(db=db, tenant_id=tenant_id)


@router.get("/trust/metrics/timeline", response_model=TrustMetricsTimeline)
def timeline_metrics_endpoint(
    days: int = Query(default=14, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tenant_id = require_tenant_id(current_user.tenant_id)
    return get_metrics_timeline(db=db, tenant_id=tenant_id, days=days)
