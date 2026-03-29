from typing import Protocol

from app.modules.trust_engine.schemas import PredictionFeatureSnapshot


class PredictionProvider(Protocol):
    def predict_purchase_probability(self, snapshot: PredictionFeatureSnapshot) -> float:
        ...

    def predict_cancellation_probability(self, snapshot: PredictionFeatureSnapshot) -> float:
        ...

    def predict_fraud_risk(self, snapshot: PredictionFeatureSnapshot) -> float:
        ...


class NullPredictionProvider:
    """
    Placeholder provider for the future AI prediction layer.
    Keeps API contracts stable before model integration.
    """

    def predict_purchase_probability(self, snapshot: PredictionFeatureSnapshot) -> float:
        return round(min(1.0, max(0.0, snapshot.trust_score / 100.0)), 4)

    def predict_cancellation_probability(self, snapshot: PredictionFeatureSnapshot) -> float:
        return round(min(1.0, max(0.0, 1.0 - (snapshot.historical_score / 100.0))), 4)

    def predict_fraud_risk(self, snapshot: PredictionFeatureSnapshot) -> float:
        baseline = 1.0 - (snapshot.trust_score / 100.0)
        return round(min(1.0, max(0.0, baseline)), 4)

