from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.models import User, Boutique, Customer, Order
from app.routes.auth import get_current_user
from app.routes import orders


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(orders.router)

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


def _seed_data():
    db = TestingSessionLocal()
    try:
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

        user_a = User(
            id=1,
            tenant_id=100,
            email="a@example.com",
            password_hash="x",
            role="user",
        )
        user_b = User(
            id=2,
            tenant_id=200,
            email="b@example.com",
            password_hash="x",
            role="user",
        )
        db.add_all([user_a, user_b])

        boutique_a = Boutique(id=1, tenant_id=100, name="A Shop", owner_id=1)
        boutique_b = Boutique(id=2, tenant_id=200, name="B Shop", owner_id=2)
        db.add_all([boutique_a, boutique_b])

        customer_a = Customer(id=1, tenant_id=100, boutique_id=1, phone="111")
        customer_b = Customer(id=2, tenant_id=200, boutique_id=2, phone="222")
        db.add_all([customer_a, customer_b])

        order_a = Order(id=1, tenant_id=100, customer_id=1, boutique_id=1, product_name="P1", price=10, status="pending")
        order_b = Order(id=2, tenant_id=200, customer_id=2, boutique_id=2, product_name="P2", price=20, status="pending")
        db.add_all([order_a, order_b])

        db.commit()
        db.refresh(user_a)
        db.refresh(user_b)
        return user_a, user_b, order_a, order_b
    finally:
        db.close()


def test_idor_block_cross_tenant_order_access():
    user_a, _, _, order_b = _seed_data()
    _current_user["value"] = user_a
    client = TestClient(app)

    response = client.get(f"/orders/{order_b.id}")
    assert response.status_code == 404


def test_orders_list_is_tenant_scoped():
    user_a, _, order_a, order_b = _seed_data()
    _current_user["value"] = user_a
    client = TestClient(app)

    response = client.get("/orders/")
    assert response.status_code == 200
    payload = response.json()
    order_ids = {row["id"] for row in payload}
    assert order_a.id in order_ids
    assert order_b.id not in order_ids
