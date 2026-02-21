from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from app.database import get_db
from app.models import User, Order, Boutique, Customer, AIDecision
from app.routes.auth import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats")
def get_dashboard_stats(
    boutique_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupérer les statistiques du dashboard
    """
    # Get user boutiques
    if boutique_id:
        boutiques = [db.get(Boutique, boutique_id)]
        if not boutiques[0] or boutiques[0].owner_id != current_user.id:
            boutiques = []
    else:
        boutiques = db.query(Boutique).filter(Boutique.owner_id == current_user.id).all()
    
    boutique_ids = [b.id for b in boutiques if b]
    
    if not boutique_ids:
        return {
            "total_orders": 0,
            "pending_orders": 0,
            "confirmed_orders": 0,
            "rejected_orders": 0,
            "total_revenue": 0,
            "total_customers": 0,
            "orders_today": 0,
            "high_risk_orders": 0
        }
    
    # Total orders
    total_orders = db.query(func.count(Order.id)).filter(
        Order.boutique_id.in_(boutique_ids)
    ).scalar()
    
    # Orders by status
    pending_orders = db.query(func.count(Order.id)).filter(
        Order.boutique_id.in_(boutique_ids),
        Order.status == "pending"
    ).scalar()
    
    confirmed_orders = db.query(func.count(Order.id)).filter(
        Order.boutique_id.in_(boutique_ids),
        Order.status == "confirmed"
    ).scalar()
    
    rejected_orders = db.query(func.count(Order.id)).filter(
        Order.boutique_id.in_(boutique_ids),
        Order.status == "rejected"
    ).scalar()
    
    # Total revenue (confirmed orders only)
    total_revenue = db.query(func.sum(Order.price)).filter(
        Order.boutique_id.in_(boutique_ids),
        Order.status == "confirmed"
    ).scalar() or 0
    
    # Total customers
    total_customers = db.query(func.count(Customer.id)).filter(
        Customer.boutique_id.in_(boutique_ids)
    ).scalar()
    
    # Orders today
    today = datetime.utcnow().date()
    orders_today = db.query(func.count(Order.id)).filter(
        Order.boutique_id.in_(boutique_ids),
        func.date(Order.created_at) == today
    ).scalar()
    
    # High risk orders (from AI decisions)
    high_risk_orders = db.query(func.count(AIDecision.id)).filter(
        AIDecision.decision == "reject",
        AIDecision.created_at >= datetime.utcnow() - timedelta(days=7)
    ).scalar()
    
    return {
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "confirmed_orders": confirmed_orders,
        "rejected_orders": rejected_orders,
        "total_revenue": float(total_revenue),
        "total_customers": total_customers,
        "orders_today": orders_today,
        "high_risk_orders": high_risk_orders
    }


@router.get("/recent-orders")
def get_recent_orders(
    limit: int = 10,
    boutique_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupérer les commandes récentes
    """
    query = db.query(Order)
    
    if boutique_id:
        boutique = db.get(Boutique, boutique_id)
        if boutique and boutique.owner_id == current_user.id:
            query = query.filter(Order.boutique_id == boutique_id)
        else:
            return []
    else:
        # Get all user boutiques
        user_boutiques = db.query(Boutique.id).filter(
            Boutique.owner_id == current_user.id
        ).all()
        boutique_ids = [b[0] for b in user_boutiques]
        query = query.filter(Order.boutique_id.in_(boutique_ids))
    
    orders = query.order_by(Order.created_at.desc()).limit(limit).all()
    
    return [
        {
            "id": o.id,
            "product_name": o.product_name,
            "price": float(o.price),
            "status": o.status,
            "created_at": o.created_at,
            "customer_id": o.customer_id
        }
        for o in orders
    ]


@router.get("/revenue-chart")
def get_revenue_chart(
    days: int = 7,
    boutique_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupérer les données du graphique de revenus (derniers X jours)
    """
    # Get boutique IDs
    if boutique_id:
        boutique = db.get(Boutique, boutique_id)
        if not boutique or boutique.owner_id != current_user.id:
            boutique_ids = []
        else:
            boutique_ids = [boutique_id]
    else:
        user_boutiques = db.query(Boutique.id).filter(
            Boutique.owner_id == current_user.id
        ).all()
        boutique_ids = [b[0] for b in user_boutiques]
    
    if not boutique_ids:
        return {"labels": [], "data": []}
    
    # Generate date range
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days-1)
    
    # Query revenue per day
    revenue_data = []
    labels = []
    
    current_date = start_date
    while current_date <= end_date:
        daily_revenue = db.query(func.sum(Order.price)).filter(
            Order.boutique_id.in_(boutique_ids),
            Order.status == "confirmed",
            func.date(Order.created_at) == current_date
        ).scalar() or 0
        
        revenue_data.append(float(daily_revenue))
        labels.append(current_date.strftime("%Y-%m-%d"))
        
        current_date += timedelta(days=1)
    
    return {
        "labels": labels,
        "data": revenue_data
    }
