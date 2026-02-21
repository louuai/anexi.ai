from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from app.database import get_db
from app.models import User, Customer, Order, AIDecision, Boutique
from app.routes.auth import get_current_user

router = APIRouter(prefix="/trust", tags=["Trust Layer"])


@router.get("/customer/{customer_id}/score")
def get_customer_trust_score(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupérer le trust score d'un client
    """
    customer = db.get(Customer, customer_id)
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client non trouvé"
        )
    
    # Verify access
    boutique = db.get(Boutique, customer.boutique_id)
    if boutique.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé"
        )
    
    # Get customer orders
    total_orders = db.query(func.count(Order.id)).filter(
        Order.customer_id == customer_id
    ).scalar()
    
    confirmed_orders = db.query(func.count(Order.id)).filter(
        Order.customer_id == customer_id,
        Order.status == "confirmed"
    ).scalar()
    
    rejected_orders = db.query(func.count(Order.id)).filter(
        Order.customer_id == customer_id,
        Order.status == "rejected"
    ).scalar()
    
    # Calculate basic trust score
    if total_orders == 0:
        trust_score = 50.0  # Neutral for new customers
        trust_level = "new"
    else:
        confirmation_rate = (confirmed_orders / total_orders) * 100
        rejection_rate = (rejected_orders / total_orders) * 100
        
        # Simple scoring algorithm
        trust_score = confirmation_rate - (rejection_rate * 2)
        trust_score = max(0, min(100, trust_score))
        
        if trust_score >= 80:
            trust_level = "high"
        elif trust_score >= 50:
            trust_level = "medium"
        else:
            trust_level = "low"
    
    return {
        "customer_id": customer_id,
        "trust_score": round(trust_score, 2),
        "trust_level": trust_level,
        "total_orders": total_orders,
        "confirmed_orders": confirmed_orders,
        "rejected_orders": rejected_orders,
        "confirmation_rate": round((confirmed_orders / total_orders * 100) if total_orders > 0 else 0, 2)
    }


@router.get("/risky-customers")
def get_risky_customers(
    boutique_id: int = None,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupérer la liste des clients à risque
    """
    # Get boutique IDs
    if boutique_id:
        boutique = db.get(Boutique, boutique_id)
        if not boutique or boutique.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Boutique non autorisée"
            )
        boutique_ids = [boutique_id]
    else:
        user_boutiques = db.query(Boutique.id).filter(
            Boutique.owner_id == current_user.id
        ).all()
        boutique_ids = [b[0] for b in user_boutiques]
    
    if not boutique_ids:
        return []
    
    # Get customers with their order stats
    customers = db.query(Customer).filter(
        Customer.boutique_id.in_(boutique_ids)
    ).all()
    
    risky_customers = []
    
    for customer in customers:
        total_orders = db.query(func.count(Order.id)).filter(
            Order.customer_id == customer.id
        ).scalar()
        
        if total_orders == 0:
            continue
        
        rejected_orders = db.query(func.count(Order.id)).filter(
            Order.customer_id == customer.id,
            Order.status == "rejected"
        ).scalar()
        
        rejection_rate = (rejected_orders / total_orders) * 100
        
        if rejection_rate > 30:  # More than 30% rejection rate
            risky_customers.append({
                "customer_id": customer.id,
                "full_name": customer.full_name,
                "phone": customer.phone,
                "total_orders": total_orders,
                "rejected_orders": rejected_orders,
                "rejection_rate": round(rejection_rate, 2)
            })
    
    # Sort by rejection rate
    risky_customers.sort(key=lambda x: x["rejection_rate"], reverse=True)
    
    return risky_customers[:limit]


@router.get("/blacklist")
def get_blacklist(
    boutique_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupérer la liste noire (customers avec 100% rejection ou pattern suspect)
    """
    risky = get_risky_customers(boutique_id, limit=100, db=db, current_user=current_user)
    
    # Filter for blacklist (rejection rate >= 70%)
    blacklist = [c for c in risky if c["rejection_rate"] >= 70]
    
    return {
        "total": len(blacklist),
        "customers": blacklist
    }
