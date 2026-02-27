from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.modules.trust.models import TrustInteraction
from app.modules.trust.repository import TrustRepository
from app.modules.trust.schemas import (
    CampaignScore,
    SegmentCount,
    TrustEvaluateRequest,
    TrustInteractionsPage,
    TrustMetricsTimeline,
    TrustScoreBreakdown,
    TrustInteractionResponse,
    TrustMetricsSummary,
)
from app.modules.trust.scoring import calculate_interaction_score
from app.modules.trust.segmentation import recommended_action_for_segment, segment_from_score


def evaluate_interaction(
    db: Session,
    tenant_id: int,
    payload: TrustEvaluateRequest,
) -> TrustInteractionResponse:
    interaction_score = calculate_interaction_score(
        confirmation_status=payload.confirmation_status,
        call_duration=payload.call_duration,
        hesitation_score=payload.hesitation_score,
    )
    segment = segment_from_score(interaction_score)
    recommended_action = recommended_action_for_segment(segment)

    record = TrustInteraction(
        tenant_id=tenant_id,
        order_id=payload.order_id,
        campaign_id=payload.campaign_id,
        client_name=payload.client_name,
        product_name=payload.product_name,
        confirmation_status=payload.confirmation_status,
        call_duration=payload.call_duration,
        hesitation_score=payload.hesitation_score,
        interaction_score=interaction_score,
        segment=segment,
        recommended_action=recommended_action,
    )

    repo = TrustRepository(db)
    saved = repo.create(record)
    return _to_response(saved)


def get_interactions(
    db: Session,
    tenant_id: int,
    limit: int,
    offset: int,
    campaign_id: str | None = None,
    segment: str | None = None,
    score_min: float | None = None,
    score_max: float | None = None,
    sort: str = "date_desc",
) -> TrustInteractionsPage:
    repo = TrustRepository(db)
    rows = repo.list_interactions(
        tenant_id=tenant_id,
        limit=limit,
        offset=offset,
        campaign_id=campaign_id,
        segment=segment,
        score_min=score_min,
        score_max=score_max,
        sort=sort,
    )
    total = repo.filtered_count(
        tenant_id=tenant_id,
        campaign_id=campaign_id,
        segment=segment,
        score_min=score_min,
        score_max=score_max,
    )
    return TrustInteractionsPage(
        items=[_to_response(row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
        has_next=(offset + len(rows)) < total,
    )


def get_metrics_summary(db: Session, tenant_id: int) -> TrustMetricsSummary:
    repo = TrustRepository(db)
    total = repo.total_count(tenant_id)
    high_risk_count = repo.segment_count(tenant_id, "HIGH_RISK")
    high_trust_count = repo.segment_count(tenant_id, "HIGH_TRUST")

    segments = [
        SegmentCount(
            segment=segment,
            total=segment_total,
            percentage=round((float(segment_total) / float(total) * 100.0), 2) if total else 0.0,
        )
        for segment, segment_total in repo.segment_counts(tenant_id)
    ]
    by_campaign = [
        CampaignScore(
            campaign_id=campaign_id,
            total_interactions=total_interactions,
            avg_interaction_score=avg_interaction_score,
            high_risk_rate=high_risk_rate,
            dominant_segment=dominant_segment,
        )
        for campaign_id, total_interactions, avg_interaction_score, high_risk_rate, dominant_segment in repo.campaign_scores(tenant_id)
    ]

    return TrustMetricsSummary(
        total_interactions=total,
        avg_interaction_score=repo.avg_score(tenant_id),
        high_risk_rate=repo.high_risk_rate(tenant_id),
        high_risk_count=high_risk_count,
        high_trust_count=high_trust_count,
        last_interaction_at=repo.last_interaction_at(tenant_id),
        segments=segments,
        by_campaign=by_campaign,
    )


def get_metrics_timeline(db: Session, tenant_id: int, days: int) -> TrustMetricsTimeline:
    safe_days = max(1, min(int(days), 90))
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=safe_days - 1)
    start_dt = datetime.combine(start_date, datetime.min.time())

    repo = TrustRepository(db)
    rows = repo.timeline_rows(tenant_id=tenant_id, start_date=start_dt)
    by_day: dict[str, tuple[float, int, int]] = {}
    for day, avg_score, high_risk_total, total in rows:
        key = str(day)
        by_day[key] = (round(float(avg_score or 0.0), 2), int(high_risk_total or 0), int(total or 0))

    labels: list[str] = []
    avg_interaction_score: list[float] = []
    high_risk_count: list[int] = []
    total_interactions: list[int] = []

    current = start_date
    while current <= end_date:
        key = current.isoformat()
        labels.append(key)
        avg_score, high_risk, total = by_day.get(key, (0.0, 0, 0))
        avg_interaction_score.append(avg_score)
        high_risk_count.append(high_risk)
        total_interactions.append(total)
        current += timedelta(days=1)

    return TrustMetricsTimeline(
        labels=labels,
        avg_interaction_score=avg_interaction_score,
        high_risk_count=high_risk_count,
        total_interactions=total_interactions,
    )


def _to_response(row: TrustInteraction) -> TrustInteractionResponse:
    breakdown = TrustScoreBreakdown(
        confirmation_component=round(
            50.0
            if str(row.confirmation_status or "").strip().lower()
            in {"confirmed", "confirm", "yes", "true", "1", "accepted"}
            else 0.0,
            2,
        ),
        duration_component=round((max(0.0, min(float(row.call_duration), 300.0)) / 300.0) * 30.0, 2),
        hesitation_component=round((1.0 - max(0.0, min(float(row.hesitation_score), 1.0))) * 20.0, 2),
    )
    return TrustInteractionResponse(
        id=row.id,
        order_id=row.order_id,
        campaign_id=row.campaign_id,
        client_name=row.client_name,
        product_name=row.product_name,
        confirmation_status=row.confirmation_status,
        call_duration=row.call_duration,
        hesitation_score=row.hesitation_score,
        interaction_score=row.interaction_score,
        segment=row.segment,
        recommended_action=row.recommended_action,
        score_breakdown=breakdown,
        created_at=row.created_at,
    )
