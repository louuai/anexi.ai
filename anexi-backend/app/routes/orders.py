from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Order, Customer, Boutique
from app.schemas import OrderCreate, OrderResponse
from app.routes.auth import get_current_user
from app.utils.tenant import require_tenant_id
from app.workers.dispatch import enqueue_task
from app.workers.decision_tasks import process_order_decision
from app.workers.analytics_tasks import refresh_analytics_for_user

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    order: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tenant_id = require_tenant_id(current_user.tenant_id)
    boutique = (
        db.query(Boutique)
        .filter(Boutique.id == order.boutique_id, Boutique.tenant_id == tenant_id)
        .first()
    )
    if not boutique or boutique.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Boutique non autorisee")

    customer = (
        db.query(Customer)
        .filter(
            Customer.id == order.customer_id,
            Customer.boutique_id == order.boutique_id,
            Customer.tenant_id == tenant_id,
        )
        .first()
    )
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client non trouve")

    new_order = Order(
        tenant_id=tenant_id,
        customer_id=order.customer_id,
        boutique_id=order.boutique_id,
        product_name=order.product_name,
        price=order.price,
        status=order.status,
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    enqueue_task(process_order_decision, new_order.id)
    enqueue_task(refresh_analytics_for_user, current_user.id, "order_created")
    return new_order


@router.get("/", response_model=List[OrderResponse])
def get_orders(
    boutique_id: int = None,
    status: str = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tenant_id = require_tenant_id(current_user.tenant_id)
    query = db.query(Order).filter(Order.tenant_id == tenant_id)

    if boutique_id:
        boutique = (
            db.query(Boutique)
            .filter(Boutique.id == boutique_id, Boutique.tenant_id == tenant_id)
            .first()
        )
        if not boutique or boutique.owner_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Boutique non autorisee")
        query = query.filter(Order.boutique_id == boutique_id)
    else:
        boutique_ids = [
            b_id
            for (b_id,) in db.query(Boutique.id)
            .filter(Boutique.owner_id == current_user.id, Boutique.tenant_id == tenant_id)
            .all()
        ]
        if not boutique_ids:
            return []
        query = query.filter(Order.boutique_id.in_(boutique_ids))

    if status:
        query = query.filter(Order.status == status)

    return query.order_by(Order.created_at.desc()).limit(limit).all()


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tenant_id = require_tenant_id(current_user.tenant_id)
    order = db.query(Order).filter(Order.id == order_id, Order.tenant_id == tenant_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Commande non trouvee")

    boutique = (
        db.query(Boutique)
        .filter(Boutique.id == order.boutique_id, Boutique.tenant_id == tenant_id)
        .first()
    )
    if not boutique or boutique.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acces non autorise")
    return order


@router.patch("/{order_id}/status")
def update_order_status(
    order_id: int,
    new_status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tenant_id = require_tenant_id(current_user.tenant_id)
    order = db.query(Order).filter(Order.id == order_id, Order.tenant_id == tenant_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Commande non trouvee")

    boutique = (
        db.query(Boutique)
        .filter(Boutique.id == order.boutique_id, Boutique.tenant_id == tenant_id)
        .first()
    )
    if not boutique or boutique.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acces non autorise")

    valid_statuses = ["pending", "confirmed", "rejected", "delivered", "cancelled"]
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Statut invalide. Valeurs possibles: {', '.join(valid_statuses)}",
        )

    order.status = new_status
    db.commit()
    db.refresh(order)

    enqueue_task(process_order_decision, order.id)
    enqueue_task(refresh_analytics_for_user, current_user.id, "order_status_updated")
    return {"message": "Statut mis a jour", "order_id": order.id, "new_status": order.status}
