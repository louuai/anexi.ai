from datetime import datetime

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.modules.trust.models import TrustInteraction


class TrustRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, interaction: TrustInteraction) -> TrustInteraction:
        self.db.add(interaction)
        self.db.commit()
        self.db.refresh(interaction)
        return interaction

    def _base_query(
        self,
        tenant_id: int,
        campaign_id: str | None = None,
        segment: str | None = None,
        score_min: float | None = None,
        score_max: float | None = None,
    ):
        query = self.db.query(TrustInteraction).filter(TrustInteraction.tenant_id == tenant_id)
        if campaign_id:
            query = query.filter(TrustInteraction.campaign_id == campaign_id)
        if segment:
            query = query.filter(TrustInteraction.segment == segment)
        if score_min is not None:
            query = query.filter(TrustInteraction.interaction_score >= score_min)
        if score_max is not None:
            query = query.filter(TrustInteraction.interaction_score <= score_max)
        return query

    def list_interactions(
        self,
        tenant_id: int,
        limit: int,
        offset: int,
        campaign_id: str | None = None,
        segment: str | None = None,
        score_min: float | None = None,
        score_max: float | None = None,
        sort: str = "date_desc",
    ) -> list[TrustInteraction]:
        query = self._base_query(
            tenant_id=tenant_id,
            campaign_id=campaign_id,
            segment=segment,
            score_min=score_min,
            score_max=score_max,
        )
        if sort == "score_asc":
            query = query.order_by(TrustInteraction.interaction_score.asc(), TrustInteraction.created_at.desc())
        elif sort == "score_desc":
            query = query.order_by(TrustInteraction.interaction_score.desc(), TrustInteraction.created_at.desc())
        elif sort == "date_asc":
            query = query.order_by(TrustInteraction.created_at.asc())
        else:
            query = query.order_by(TrustInteraction.created_at.desc())
        return (
            query
            .offset(offset)
            .limit(limit)
            .all()
        )

    def total_count(self, tenant_id: int) -> int:
        return (
            self.db.query(func.count(TrustInteraction.id))
            .filter(TrustInteraction.tenant_id == tenant_id)
            .scalar()
            or 0
        )

    def filtered_count(
        self,
        tenant_id: int,
        campaign_id: str | None = None,
        segment: str | None = None,
        score_min: float | None = None,
        score_max: float | None = None,
    ) -> int:
        return int(
            self._base_query(
                tenant_id=tenant_id,
                campaign_id=campaign_id,
                segment=segment,
                score_min=score_min,
                score_max=score_max,
            )
            .with_entities(func.count(TrustInteraction.id))
            .scalar()
            or 0
        )

    def avg_score(self, tenant_id: int) -> float:
        value = (
            self.db.query(func.avg(TrustInteraction.interaction_score))
            .filter(TrustInteraction.tenant_id == tenant_id)
            .scalar()
        )
        return round(float(value or 0.0), 2)

    def segment_counts(self, tenant_id: int) -> list[tuple[str, int]]:
        rows = (
            self.db.query(TrustInteraction.segment, func.count(TrustInteraction.id))
            .filter(TrustInteraction.tenant_id == tenant_id)
            .group_by(TrustInteraction.segment)
            .all()
        )
        return [(segment, int(total)) for segment, total in rows]

    def campaign_scores(self, tenant_id: int) -> list[tuple[str, int, float, float, str]]:
        aggregate_rows = (
            self.db.query(
                TrustInteraction.campaign_id,
                func.count(TrustInteraction.id),
                func.avg(TrustInteraction.interaction_score),
                func.sum(case((TrustInteraction.segment == "HIGH_RISK", 1), else_=0)),
            )
            .filter(
                TrustInteraction.tenant_id == tenant_id,
                TrustInteraction.campaign_id.isnot(None),
            )
            .group_by(TrustInteraction.campaign_id)
            .order_by(func.avg(TrustInteraction.interaction_score).desc())
            .all()
        )
        segment_rows = (
            self.db.query(
                TrustInteraction.campaign_id,
                TrustInteraction.segment,
                func.count(TrustInteraction.id),
            )
            .filter(
                TrustInteraction.tenant_id == tenant_id,
                TrustInteraction.campaign_id.isnot(None),
            )
            .group_by(TrustInteraction.campaign_id, TrustInteraction.segment)
            .all()
        )
        dominant_by_campaign: dict[str, tuple[str, int]] = {}
        for campaign_id, segment, total in segment_rows:
            key = str(campaign_id)
            current = dominant_by_campaign.get(key)
            candidate = (str(segment), int(total))
            if current is None or candidate[1] > current[1]:
                dominant_by_campaign[key] = candidate

        result: list[tuple[str, int, float, float, str]] = []
        for campaign_id, total, avg_score, high_risk_total in aggregate_rows:
            campaign_key = str(campaign_id)
            total_int = int(total or 0)
            high_risk_rate = 0.0 if total_int == 0 else round((float(high_risk_total or 0) / total_int) * 100.0, 2)
            dominant_segment = dominant_by_campaign.get(campaign_key, ("UNKNOWN", 0))[0]
            result.append(
                (
                    campaign_key,
                    total_int,
                    round(float(avg_score or 0.0), 2),
                    high_risk_rate,
                    dominant_segment,
                )
            )
        return result

    def high_risk_rate(self, tenant_id: int) -> float:
        total = self.total_count(tenant_id)
        if total == 0:
            return 0.0
        high_risk = (
            self.db.query(func.count(TrustInteraction.id))
            .filter(
                TrustInteraction.tenant_id == tenant_id,
                TrustInteraction.segment == "HIGH_RISK",
            )
            .scalar()
            or 0
        )
        return round((float(high_risk) / float(total)) * 100.0, 2)

    def segment_count(self, tenant_id: int, segment: str) -> int:
        return int(
            self.db.query(func.count(TrustInteraction.id))
            .filter(
                TrustInteraction.tenant_id == tenant_id,
                TrustInteraction.segment == segment,
            )
            .scalar()
            or 0
        )

    def last_interaction_at(self, tenant_id: int) -> datetime | None:
        return (
            self.db.query(func.max(TrustInteraction.created_at))
            .filter(TrustInteraction.tenant_id == tenant_id)
            .scalar()
        )

    def timeline_rows(self, tenant_id: int, start_date: datetime):
        return (
            self.db.query(
                func.date(TrustInteraction.created_at).label("day"),
                func.avg(TrustInteraction.interaction_score).label("avg_score"),
                func.sum(case((TrustInteraction.segment == "HIGH_RISK", 1), else_=0)).label("high_risk_total"),
                func.count(TrustInteraction.id).label("total"),
            )
            .filter(
                TrustInteraction.tenant_id == tenant_id,
                TrustInteraction.created_at >= start_date,
            )
            .group_by(func.date(TrustInteraction.created_at))
            .order_by(func.date(TrustInteraction.created_at).asc())
            .all()
        )
