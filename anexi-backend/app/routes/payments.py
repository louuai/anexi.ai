from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Boutique, Customer, Payment
from app.routes.auth import get_current_user
from app.schemas import PaymentCreate, PaymentResponse

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/checkout", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(
    payload: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    boutique = db.get(Boutique, payload.boutique_id)
    if not boutique or boutique.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Boutique non autorisee pour ce compte",
        )

    customer = db.get(Customer, payload.customer_id)
    if not customer or customer.boutique_id != boutique.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer non valide pour cette boutique",
        )

    payment = Payment(
        user_id=current_user.id,
        boutique_id=boutique.id,
        customer_id=customer.id,
        plan=payload.plan,
        amount=payload.amount,
        payment_method=payload.payment_method,
        status="confirmed",
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


@router.get("/", response_model=List[PaymentResponse])
def list_my_payments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Payment)
        .filter(Payment.user_id == current_user.id)
        .order_by(Payment.created_at.desc())
        .all()
    )
