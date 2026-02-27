import uuid

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.models import User
from app.modules.trust import models as trust_models  # noqa: F401
from app.routes.auth import get_current_user
from app.routes import trust


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(trust.router)

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
        user_b = User(id=2, tenant_id=200, email="tenant-b@example.com", password_hash="x", role="user")
        db.add_all([user_a, user_b])
        db.commit()
        db.refresh(user_a)
        db.refresh(user_b)
        return user_a, user_b
    finally:
        db.close()


def _evaluate(client: TestClient, order_id: uuid.UUID, confirmation_status: str, campaign_id: str):
    return client.post(
        "/internal/trust/evaluate",
        json={
            "order_id": str(order_id),
            "campaign_id": campaign_id,
            "client_name": "John Client",
            "product_name": "Sample Product",
            "confirmation_status": confirmation_status,
            "call_duration": 180.0,
            "hesitation_score": 0.2,
        },
    )


def test_trust_interactions_are_tenant_scoped():
    user_a, user_b = _seed_users()
    client = TestClient(app)

    _current_user["value"] = user_a
    response_a = _evaluate(client, uuid.uuid4(), "confirmed", "camp-a")
    assert response_a.status_code == 200

    _current_user["value"] = user_b
    response_b = _evaluate(client, uuid.uuid4(), "rejected", "camp-b")
    assert response_b.status_code == 200

    _current_user["value"] = user_a
    list_response = client.get("/trust/interactions")
    assert list_response.status_code == 200
    payload = list_response.json()
    assert payload["total"] == 1
    assert len(payload["items"]) == 1
    assert payload["items"][0]["campaign_id"] == "camp-a"
    assert payload["items"][0]["client_name"] == "John Client"
    assert payload["items"][0]["score_breakdown"]["duration_component"] > 0


def test_trust_summary_is_tenant_scoped():
    user_a, user_b = _seed_users()
    client = TestClient(app)

    _current_user["value"] = user_a
    _evaluate(client, uuid.uuid4(), "confirmed", "camp-a")

    _current_user["value"] = user_b
    _evaluate(client, uuid.uuid4(), "rejected", "camp-b")

    _current_user["value"] = user_a
    summary_response = client.get("/trust/metrics/summary")
    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert summary["total_interactions"] == 1
    assert summary["high_trust_count"] == 1
    assert summary["high_risk_count"] == 0
    assert summary["last_interaction_at"] is not None
    assert len(summary["by_campaign"]) == 1
    assert summary["by_campaign"][0]["campaign_id"] == "camp-a"
    assert summary["by_campaign"][0]["total_interactions"] == 1
    assert summary["segments"][0]["percentage"] == 100.0
