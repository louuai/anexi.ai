from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Boutique, Customer
from app.schemas import BoutiqueCreate, BoutiqueResponse, CustomerCreate, CustomerResponse
from app.routes.auth import get_current_user

router = APIRouter(prefix="/boutiques", tags=["Boutiques"])


@router.post("/", response_model=BoutiqueResponse, status_code=status.HTTP_201_CREATED)
def create_boutique(
    boutique: BoutiqueCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Créer une nouvelle boutique
    """
    new_boutique = Boutique(
        name=boutique.name,
        owner_id=current_user.id
    )
    
    db.add(new_boutique)
    db.commit()
    db.refresh(new_boutique)
    
    return new_boutique


@router.get("/", response_model=List[BoutiqueResponse])
def get_boutiques(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupérer toutes les boutiques de l'utilisateur
    """
    boutiques = db.query(Boutique).filter(Boutique.owner_id == current_user.id).all()
    return boutiques


@router.get("/{boutique_id}", response_model=BoutiqueResponse)
def get_boutique(
    boutique_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupérer une boutique spécifique
    """
    boutique = db.get(Boutique, boutique_id)
    
    if not boutique:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Boutique non trouvée"
        )
    
    if boutique.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé"
        )
    
    return boutique


@router.post("/{boutique_id}/customers", response_model=CustomerResponse)
def create_customer(
    boutique_id: int,
    customer: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Ajouter un nouveau client à une boutique
    """
    # Verify boutique ownership
    boutique = db.get(Boutique, boutique_id)
    if not boutique or boutique.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Boutique non autorisée"
        )
    
    # Check if customer already exists (by phone)
    existing = db.query(Customer).filter(
        Customer.phone == customer.phone,
        Customer.boutique_id == boutique_id
    ).first()
    
    if existing:
        return existing
    
    # Create new customer
    new_customer = Customer(
        full_name=customer.full_name,
        phone=customer.phone,
        email=customer.email,
        boutique_id=boutique_id
    )
    
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)
    
    return new_customer


@router.get("/{boutique_id}/customers", response_model=List[CustomerResponse])
def get_customers(
    boutique_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupérer tous les clients d'une boutique
    """
    # Verify boutique ownership
    boutique = db.get(Boutique, boutique_id)
    if not boutique or boutique.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Boutique non autorisée"
        )
    
    customers = db.query(Customer).filter(Customer.boutique_id == boutique_id).all()
    return customers
