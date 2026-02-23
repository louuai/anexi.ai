from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Order, Customer, Boutique
from app.schemas import OrderCreate, OrderResponse, OrderWithDecision
from app.routes.auth import get_current_user
from app.workers.dispatch import enqueue_task
from app.workers.decision_tasks import process_order_decision
from app.workers.analytics_tasks import refresh_analytics_for_user

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    order: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Créer une nouvelle commande
    """
    # Verify boutique belongs to current user
    boutique = db.get(Boutique, order.boutique_id)
    if not boutique or boutique.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Boutique non autorisée"
        )
    
    # Verify customer exists
    customer = db.get(Customer, order.customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client non trouvé"
        )
    
    # Create order
    new_order = Order(
        customer_id=order.customer_id,
        boutique_id=order.boutique_id,
        product_name=order.product_name,
        price=order.price,
        status=order.status
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
    current_user: User = Depends(get_current_user)
):
    """
    Récupérer les commandes (avec filtres optionnels)
    """
    query = db.query(Order)
    
    # Filter by boutique if specified
    if boutique_id:
        boutique = db.get(Boutique, boutique_id)
        if not boutique or boutique.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Boutique non autorisée"
            )
        query = query.filter(Order.boutique_id == boutique_id)
    else:
        # Get all boutiques owned by current user
        user_boutiques = db.query(Boutique.id).filter(Boutique.owner_id == current_user.id).all()
        boutique_ids = [b[0] for b in user_boutiques]
        query = query.filter(Order.boutique_id.in_(boutique_ids))
    
    # Filter by status if specified
    if status:
        query = query.filter(Order.status == status)
    
    # Limit results
    orders = query.order_by(Order.created_at.desc()).limit(limit).all()
    
    return orders


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupérer une commande spécifique
    """
    order = db.get(Order, order_id)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Commande non trouvée"
        )
    
    # Verify access
    boutique = db.get(Boutique, order.boutique_id)
    if boutique.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé"
        )
    
    return order


@router.patch("/{order_id}/status")
def update_order_status(
    order_id: int,
    new_status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mettre à jour le statut d'une commande
    """
    order = db.get(Order, order_id)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Commande non trouvée"
        )
    
    # Verify access
    boutique = db.get(Boutique, order.boutique_id)
    if boutique.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé"
        )
    
    # Valid statuses
    valid_statuses = ["pending", "confirmed", "rejected", "delivered", "cancelled"]
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Statut invalide. Valeurs possibles: {', '.join(valid_statuses)}"
        )
    
    order.status = new_status
    db.commit()
    db.refresh(order)

    enqueue_task(process_order_decision, order.id)
    enqueue_task(refresh_analytics_for_user, current_user.id, "order_status_updated")
    
    return {
        "message": "Statut mis à jour",
        "order_id": order.id,
        "new_status": order.status
    }
