from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from app.database import get_db
from app.models import User, UserProfile, Boutique, Customer, Order, Call, AdsInsight, Payment
from app.routes.auth import get_current_user
from app.utils.security import hash_password
from app.utils.tenant import require_tenant_id

router = APIRouter(prefix="/admin", tags=["Admin"])


def _is_admin_user(user: User) -> bool:
    return (user.role or "").strip().lower() in {"admin", "super_admin", "founder"}


def _is_platform_admin(user: User) -> bool:
    return (user.role or "").strip().lower() in {"super_admin", "founder"}


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if not _is_admin_user(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


def _scope_tenant_id(current_user: User) -> int | None:
    if _is_platform_admin(current_user):
        return None
    return require_tenant_id(current_user.tenant_id)


class AdminUserCreate(BaseModel):
    full_name: Optional[str] = None
    email: EmailStr
    password: str
    role: str = "user"


class AdminUserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[str] = None


class AdminUserOut(BaseModel):
    id: int
    full_name: Optional[str]
    email: str
    role: str
    created_at: Optional[str]


@router.get("/overview")
def admin_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    tenant_id = _scope_tenant_id(current_user)

    users_q = db.query(User)
    boutiques_q = db.query(Boutique)
    customers_q = db.query(Customer)
    orders_q = db.query(Order)
    payments_q = db.query(Payment)
    if tenant_id is not None:
        users_q = users_q.filter(User.tenant_id == tenant_id)
        boutiques_q = boutiques_q.filter(Boutique.tenant_id == tenant_id)
        customers_q = customers_q.filter(Customer.tenant_id == tenant_id)
        orders_q = orders_q.filter(Order.tenant_id == tenant_id)
        payments_q = payments_q.filter(Payment.tenant_id == tenant_id)

    total_users = users_q.with_entities(func.count(User.id)).scalar() or 0
    total_boutiques = boutiques_q.with_entities(func.count(Boutique.id)).scalar() or 0
    total_customers = customers_q.with_entities(func.count(Customer.id)).scalar() or 0
    total_orders = orders_q.with_entities(func.count(Order.id)).scalar() or 0
    total_payments = payments_q.with_entities(func.count(Payment.id)).scalar() or 0
    total_revenue = payments_q.with_entities(func.sum(Payment.amount)).scalar() or 0

    recent_users = users_q.order_by(User.created_at.desc()).limit(8).all()
    recent_payments = payments_q.order_by(Payment.created_at.desc()).limit(8).all()

    return {
        "totals": {
            "users": int(total_users),
            "boutiques": int(total_boutiques),
            "customers": int(total_customers),
            "orders": int(total_orders),
            "payments": int(total_payments),
            "revenue": float(total_revenue),
        },
        "recent_users": [
            {
                "id": u.id,
                "full_name": u.full_name,
                "email": u.email,
                "role": u.role,
                "created_at": u.created_at,
            }
            for u in recent_users
        ],
        "recent_payments": [
            {
                "id": p.id,
                "user_id": p.user_id,
                "boutique_id": p.boutique_id,
                "customer_id": p.customer_id,
                "plan": p.plan,
                "amount": float(p.amount),
                "payment_method": p.payment_method,
                "status": p.status,
                "created_at": p.created_at,
            }
            for p in recent_payments
        ],
    }


@router.get("/users", response_model=List[AdminUserOut])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    tenant_id = _scope_tenant_id(current_user)
    query = db.query(User)
    if tenant_id is not None:
        query = query.filter(User.tenant_id == tenant_id)
    users = query.order_by(User.created_at.desc()).all()
    return [
        AdminUserOut(
            id=u.id,
            full_name=u.full_name,
            email=u.email,
            role=u.role,
            created_at=u.created_at.isoformat() if u.created_at else None,
        )
        for u in users
    ]


@router.get("/users/{user_id}", response_model=AdminUserOut)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    tenant_id = _scope_tenant_id(current_user)
    user = db.get(User, user_id)
    if not user or (tenant_id is not None and user.tenant_id != tenant_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return AdminUserOut(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        role=user.role,
        created_at=user.created_at.isoformat() if user.created_at else None,
    )


@router.post("/users", response_model=AdminUserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: AdminUserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    scope_tenant_id = _scope_tenant_id(current_user)
    user = User(
        tenant_id=scope_tenant_id,
        full_name=payload.full_name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=(payload.role or "user").lower(),
    )
    db.add(user)
    try:
        db.flush()
        if user.tenant_id is None:
            user.tenant_id = user.id
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")
    return AdminUserOut(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        role=user.role,
        created_at=user.created_at.isoformat() if user.created_at else None,
    )


@router.put("/users/{user_id}", response_model=AdminUserOut)
def update_user(
    user_id: int,
    payload: AdminUserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    tenant_id = _scope_tenant_id(current_user)
    user = db.get(User, user_id)
    if not user or (tenant_id is not None and user.tenant_id != tenant_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if payload.email is not None:
        user.email = payload.email
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.role is not None:
        user.role = payload.role.lower()
    if payload.password:
        user.password_hash = hash_password(payload.password)

    if user.id == current_user.id and user.role not in {"admin", "super_admin", "founder"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove your own admin role")

    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")

    return AdminUserOut(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        role=user.role,
        created_at=user.created_at.isoformat() if user.created_at else None,
    )


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    tenant_id = _scope_tenant_id(current_user)
    user = db.get(User, user_id)
    if not user or (tenant_id is not None and user.tenant_id != tenant_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete your own account")

    try:
        boutique_ids = [
            b_id
            for (b_id,) in db.query(Boutique.id)
            .filter(Boutique.owner_id == user.id, Boutique.tenant_id == user.tenant_id)
            .all()
        ]
        customer_ids: list[int] = []
        order_ids: list[int] = []
        if boutique_ids:
            customer_ids = [
                c_id
                for (c_id,) in db.query(Customer.id)
                .filter(Customer.boutique_id.in_(boutique_ids), Customer.tenant_id == user.tenant_id)
                .all()
            ]
            order_ids = [
                o_id
                for (o_id,) in db.query(Order.id)
                .filter(Order.boutique_id.in_(boutique_ids), Order.tenant_id == user.tenant_id)
                .all()
            ]

        if order_ids:
            db.query(Call).filter(Call.order_id.in_(order_ids), Call.tenant_id == user.tenant_id).delete(
                synchronize_session=False
            )
        payment_filters = [Payment.user_id == user.id]
        if boutique_ids:
            payment_filters.append(Payment.boutique_id.in_(boutique_ids))
        if customer_ids:
            payment_filters.append(Payment.customer_id.in_(customer_ids))
        db.query(Payment).filter(Payment.tenant_id == user.tenant_id, or_(*payment_filters)).delete(
            synchronize_session=False
        )
        if order_ids:
            db.query(Order).filter(Order.id.in_(order_ids), Order.tenant_id == user.tenant_id).delete(
                synchronize_session=False
            )
        if customer_ids:
            db.query(Customer).filter(Customer.id.in_(customer_ids), Customer.tenant_id == user.tenant_id).delete(
                synchronize_session=False
            )
        if boutique_ids:
            db.query(AdsInsight).filter(
                AdsInsight.boutique_id.in_(boutique_ids), AdsInsight.tenant_id == user.tenant_id
            ).delete(synchronize_session=False)
            db.query(Boutique).filter(Boutique.id.in_(boutique_ids), Boutique.tenant_id == user.tenant_id).delete(
                synchronize_session=False
            )
        db.query(UserProfile).filter(
            UserProfile.user_id == user.id, UserProfile.tenant_id == user.tenant_id
        ).delete(synchronize_session=False)
        db.delete(user)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete this user because related data still exists",
        )

    return {"message": "User deleted"}
