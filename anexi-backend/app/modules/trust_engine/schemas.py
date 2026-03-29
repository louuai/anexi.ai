from datetime import datetime

from pydantic import BaseModel, Field


class ContextualSignal(BaseModel):
    event_type: str = Field(min_length=3, max_length=64)
    confirmation_status: str | None = None
    call_duration: float | None = Field(default=None, ge=0)
    hesitation_score: float | None = Field(default=None, ge=0, le=1)


class TrustScoreRequest(BaseModel):
    customer_id: str = Field(min_length=1, max_length=128)
    merchant_id: int | None = Field(default=None, gt=0)
    contextual_signal: ContextualSignal
    window_days: int = Field(default=30, ge=1, le=365)


class HistoricalSignalSummary(BaseModel):
    purchases: int
    cancellations: int
    refunds: int
    calls_confirmed: int
    calls_failed: int
    interactions: int
    behavioral_consistency: float


class TrustScoreResponse(BaseModel):
    tenant_id: int
    merchant_id: int | None
    customer_id: str
    contextual_score: float
    historical_score: float
    trust_score: float
    computed_at: datetime
    summary: HistoricalSignalSummary


class PredictionFeatureSnapshot(BaseModel):
    tenant_id: int
    merchant_id: int | None
    customer_id: str
    trust_score: float
    contextual_score: float
    historical_score: float
    interactions_30d: int
    refunds_30d: int
    cancellations_30d: int

