from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Boutique, Customer
from app.schemas import BoutiqueCreate, BoutiqueResponse, CustomerCreate, CustomerResponse
from app.routes.auth import get_current_user
from app.utils.tenant import require_tenant_id

router = APIRouter(prefix="/boutiques", tags=["Boutiques"])


@router.post("/", response_model=BoutiqueResponse, status_code=status.HTTP_201_CREATED)
def create_boutique(
    boutique: BoutiqueCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tenant_id = require_tenant_id(current_user.tenant_id)
    new_boutique = Boutique(
        tenant_id=tenant_id,
        name=boutique.name,
        owner_id=current_user.id,
    )

    db.add(new_boutique)
    db.commit()
    db.refresh(new_boutique)
    return new_boutique


@router.get("/", response_model=List[BoutiqueResponse])
def get_boutiques(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tenant_id = require_tenant_id(current_user.tenant_id)
    return (
        db.query(Boutique)
        .filter(Boutique.owner_id == current_user.id, Boutique.tenant_id == tenant_id)
        .all()
    )


@router.get("/{boutique_id}", response_model=BoutiqueResponse)
def get_boutique(
    boutique_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tenant_id = require_tenant_id(current_user.tenant_id)
    boutique = (
        db.query(Boutique)
        .filter(Boutique.id == boutique_id, Boutique.tenant_id == tenant_id)
        .first()
    )
    if not boutique:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Boutique non trouvee")
    if boutique.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acces non autorise")
    return boutique


@router.post("/{boutique_id}/customers", response_model=CustomerResponse)
def create_customer(
    boutique_id: int,
    customer: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tenant_id = require_tenant_id(current_user.tenant_id)
    boutique = (
        db.query(Boutique)
        .filter(Boutique.id == boutique_id, Boutique.tenant_id == tenant_id)
        .first()
    )
    if not boutique or boutique.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Boutique non autorisee")

    existing = (
        db.query(Customer)
        .filter(
            Customer.phone == customer.phone,
            Customer.boutique_id == boutique_id,
            Customer.tenant_id == tenant_id,
        )
        .first()
    )
    if existing:
        return existing

    new_customer = Customer(
        tenant_id=tenant_id,
        full_name=customer.full_name,
        phone=customer.phone,
        email=customer.email,
        boutique_id=boutique_id,
    )
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)
    return new_customer


@router.get("/{boutique_id}/customers", response_model=List[CustomerResponse])
def get_customers(
    boutique_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tenant_id = require_tenant_id(current_user.tenant_id)
    boutique = (
        db.query(Boutique)
        .filter(Boutique.id == boutique_id, Boutique.tenant_id == tenant_id)
        .first()
    )
    if not boutique or boutique.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Boutique non autorisee")

    return (
        db.query(Customer)
        .filter(Customer.boutique_id == boutique_id, Customer.tenant_id == tenant_id)
        .all()
    )
