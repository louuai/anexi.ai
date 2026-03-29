from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.models import User
from app.modules.events import models as event_models  # noqa: F401
from app.routes import events, timeline
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
app.include_router(timeline.router)

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


def test_ingestion_is_tenant_scoped_and_normalized():
    user_a, user_b = _seed_users()
    client = TestClient(app)

    _current_user["value"] = user_a
    response = client.post(
        "/events/ingestion/webhooks",
        json={
            "source_channel": "webhook",
            "payload": {
                "event_type": "order_created",
                "raw_event": {"customer_id": "cust-01", "platform": "shopify"},
                "event_payload": {"order_id": "ORD-001"},
            },
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["event"]["tenant_id"] == 100
    assert payload["event"]["event_type"] == "customer_purchase"

    _current_user["value"] = user_b
    list_response = client.get("/events/store/customer/cust-01")
    assert list_response.status_code == 200
    assert list_response.json() == []


def test_timeline_reconstructs_chronological_sequence():
    user_a, _ = _seed_users()
    client = TestClient(app)
    _current_user["value"] = user_a

    inputs = [
        ("tracking", "customer_view_product"),
        ("tracking", "customer_add_to_cart"),
        ("internal", "customer_purchase"),
    ]
    for channel, event_type in inputs:
        response = client.post(
            f"/events/ingestion/{channel}",
            json={
                "source_channel": channel,
                "payload": {
                    "customer_id": "cust-timeline",
                    "event_type": event_type,
                    "source_platform": "shopify",
                    "event_payload": {"step": event_type},
                },
            },
        )
        assert response.status_code == 200

    timeline_response = client.get("/timeline/customers/cust-timeline")
    assert timeline_response.status_code == 200
    items = timeline_response.json()["items"]
    assert [item["event_type"] for item in items] == [x[1] for x in inputs]

