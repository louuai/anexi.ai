from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.modules.events import event_types
from app.modules.timeline.service import build_customer_timeline
from app.modules.trust.scoring import calculate_interaction_score
from app.modules.trust_engine.schemas import (
    HistoricalSignalSummary,
    PredictionFeatureSnapshot,
    TrustScoreRequest,
    TrustScoreResponse,
)


_POSITIVE_EVENTS = {event_types.CUSTOMER_PURCHASE, event_types.CALL_CONFIRMED}
_NEGATIVE_EVENTS = {event_types.ORDER_CANCELLED, event_types.ORDER_REFUNDED, event_types.CALL_FAILED}


def _score_contextual(payload: TrustScoreRequest) -> float:
    signal = payload.contextual_signal
    if signal.call_duration is not None and signal.hesitation_score is not None and signal.confirmation_status is not None:
        return round(
            calculate_interaction_score(
                confirmation_status=signal.confirmation_status,
                call_duration=signal.call_duration,
                hesitation_score=signal.hesitation_score,
            ),
            2,
        )
    if signal.event_type in _POSITIVE_EVENTS:
        return 85.0
    if signal.event_type in _NEGATIVE_EVENTS:
        return 20.0
    return 50.0


def _score_historical(events: list[str]) -> tuple[float, HistoricalSignalSummary]:
    purchases = sum(1 for event in events if event == event_types.CUSTOMER_PURCHASE)
    cancellations = sum(1 for event in events if event == event_types.ORDER_CANCELLED)
    refunds = sum(1 for event in events if event == event_types.ORDER_REFUNDED)
    calls_confirmed = sum(1 for event in events if event == event_types.CALL_CONFIRMED)
    calls_failed = sum(1 for event in events if event == event_types.CALL_FAILED)
    interactions = len(events)

    if interactions == 0:
        summary = HistoricalSignalSummary(
            purchases=0,
            cancellations=0,
            refunds=0,
            calls_confirmed=0,
            calls_failed=0,
            interactions=0,
            behavioral_consistency=0.0,
        )
        return 50.0, summary

    raw = 50.0
    raw += purchases * 10.0
    raw += calls_confirmed * 8.0
    raw -= cancellations * 14.0
    raw -= refunds * 18.0
    raw -= calls_failed * 10.0

    positives = purchases + calls_confirmed
    negatives = cancellations + refunds + calls_failed
    consistency = positives / (positives + negatives) if (positives + negatives) > 0 else 0.5
    raw += (consistency - 0.5) * 20.0

    score = round(max(0.0, min(100.0, raw)), 2)
    summary = HistoricalSignalSummary(
        purchases=purchases,
        cancellations=cancellations,
        refunds=refunds,
        calls_confirmed=calls_confirmed,
        calls_failed=calls_failed,
        interactions=interactions,
        behavioral_consistency=round(consistency * 100.0, 2),
    )
    return score, summary


def evaluate_trust_score(
    db: Session,
    tenant_id: int,
    payload: TrustScoreRequest,
) -> tuple[TrustScoreResponse, PredictionFeatureSnapshot]:
    end_at = datetime.utcnow()
    start_at = end_at - timedelta(days=payload.window_days)

    timeline = build_customer_timeline(
        db=db,
        tenant_id=tenant_id,
        customer_id=payload.customer_id,
        merchant_id=payload.merchant_id,
        start_at=start_at,
        end_at=end_at,
        limit=5000,
    )
    event_types = [item.event_type for item in timeline.items]

    contextual_score = _score_contextual(payload)
    historical_score, summary = _score_historical(event_types)
    trust_score = round((0.4 * contextual_score) + (0.6 * historical_score), 2)

    response = TrustScoreResponse(
        tenant_id=tenant_id,
        merchant_id=payload.merchant_id,
        customer_id=payload.customer_id,
        contextual_score=contextual_score,
        historical_score=historical_score,
        trust_score=trust_score,
        computed_at=end_at,
        summary=summary,
    )
    snapshot = PredictionFeatureSnapshot(
        tenant_id=tenant_id,
        merchant_id=payload.merchant_id,
        customer_id=payload.customer_id,
        trust_score=trust_score,
        contextual_score=contextual_score,
        historical_score=historical_score,
        interactions_30d=summary.interactions,
        refunds_30d=summary.refunds,
        cancellations_30d=summary.cancellations,
    )
    return response, snapshot
