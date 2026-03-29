from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.models import User
from app.modules.events import models as event_models  # noqa: F401
from app.routes import events, trust_engine
from app.routes.auth import get_current_user


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(events.router)
app.include_router(trust_engine.router)

_current_user = {"value": None}


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def override_get_current_user():
    return _current_user["value"]


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user


def _seed_users():
    db = TestingSessionLocal()
    try:
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        user_a = User(id=1, tenant_id=100, email="tenant-a@example.com", password_hash="x", role="user")
        db.add(user_a)
        db.commit()
        db.refresh(user_a)
        return user_a
    finally:
        db.close()


def test_trust_engine_uses_contextual_and_historical_scores():
    user_a = _seed_users()
    client = TestClient(app)
    _current_user["value"] = user_a

    history = [
        "customer_purchase",
        "call_confirmed",
        "order_refunded",
    ]
    for event_type in history:
        response = client.post(
            "/events/ingestion/internal",
            json={
                "source_channel": "internal",
                "payload": {
                    "customer_id": "cust-trust",
                    "event_type": event_type,
                    "source_platform": "internal",
                    "event_payload": {},
                },
            },
        )
        assert response.status_code == 200

    score_response = client.post(
        "/trust-engine/score",
        json={
            "customer_id": "cust-trust",
            "contextual_signal": {
                "event_type": "customer_purchase",
                "confirmation_status": "confirmed",
                "call_duration": 200,
                "hesitation_score": 0.2,
            },
            "window_days": 30,
        },
    )
    assert score_response.status_code == 200
    payload = score_response.json()
    assert payload["contextual_score"] > 0
    assert payload["historical_score"] > 0
    expected = round((0.4 * payload["contextual_score"]) + (0.6 * payload["historical_score"]), 2)
    assert payload["trust_score"] == expected

