from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.modules.trust_engine.prediction import NullPredictionProvider
from app.modules.trust_engine.schemas import TrustScoreRequest, TrustScoreResponse
from app.modules.trust_engine.service import evaluate_trust_score
from app.routes.auth import get_current_user
from app.utils.tenant import require_tenant_id

router = APIRouter(tags=["Trust Engine"])


@router.post("/trust-engine/score", response_model=TrustScoreResponse)
def score_customer_trust(
    payload: TrustScoreRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tenant_id = require_tenant_id(current_user.tenant_id)
    response, _ = evaluate_trust_score(
        db=db,
        tenant_id=tenant_id,
        payload=payload,
    )
    return response


@router.post("/trust-engine/prediction-preview", response_model=dict)
def prediction_preview(
    payload: TrustScoreRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tenant_id = require_tenant_id(current_user.tenant_id)
    response, snapshot = evaluate_trust_score(db=db, tenant_id=tenant_id, payload=payload)
    predictor = NullPredictionProvider()
    return {
        "trust_score": response.trust_score,
        "purchase_probability": predictor.predict_purchase_probability(snapshot),
        "cancellation_probability": predictor.predict_cancellation_probability(snapshot),
        "fraud_risk": predictor.predict_fraud_risk(snapshot),
        "note": "Preview baseline using placeholder provider. Replace with ML provider in AI layer.",
    }

