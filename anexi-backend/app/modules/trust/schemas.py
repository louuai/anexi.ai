import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class TrustEvaluateRequest(BaseModel):
    order_id: uuid.UUID
    campaign_id: str | None = None
    client_name: str | None = None
    product_name: str | None = None
    confirmation_status: str
    call_duration: float = Field(ge=0)
    hesitation_score: float = Field(ge=0, le=1)


class TrustScoreBreakdown(BaseModel):
    confirmation_component: float
    duration_component: float
    hesitation_component: float


class TrustInteractionResponse(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    campaign_id: str | None = None
    client_name: str | None = None
    product_name: str | None = None
    confirmation_status: str
    call_duration: float
    hesitation_score: float
    interaction_score: float
    segment: str
    recommended_action: str
    score_breakdown: TrustScoreBreakdown
    created_at: datetime

    model_config = {"from_attributes": True}


class SegmentCount(BaseModel):
    segment: str
    total: int
    percentage: float


class CampaignScore(BaseModel):
    campaign_id: str
    total_interactions: int
    avg_interaction_score: float
    high_risk_rate: float
    dominant_segment: str


class TrustMetricsSummary(BaseModel):
    total_interactions: int
    avg_interaction_score: float
    high_risk_rate: float
    high_risk_count: int
    high_trust_count: int
    last_interaction_at: datetime | None = None
    segments: list[SegmentCount]
    by_campaign: list[CampaignScore]


class TrustInteractionsPage(BaseModel):
    items: list[TrustInteractionResponse]
    total: int
    limit: int
    offset: int
    has_next: bool


class TrustMetricsTimeline(BaseModel):
    labels: list[str]
    avg_interaction_score: list[float]
    high_risk_count: list[int]
    total_interactions: list[int]
