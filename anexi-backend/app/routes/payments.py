from typing import List
import os

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Boutique, Customer, Payment
from app.routes.auth import get_current_user
from app.schemas import PaymentCreate, PaymentResponse
from app.workers.dispatch import enqueue_task
from app.workers.analytics_tasks import refresh_analytics_for_user
from app.workers.payment_tasks import process_payment_webhook_event

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

    enqueue_task(refresh_analytics_for_user, current_user.id, "payment_checkout")
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


@router.post("/webhook", status_code=status.HTTP_202_ACCEPTED)
def payment_webhook(
    payload: dict,
    webhook_secret: str | None = Header(default=None, alias="X-Webhook-Secret"),
):
    """
    Receive payment provider webhook and process asynchronously.
    """
    expected_secret = os.getenv("PAYMENT_WEBHOOK_SECRET", "").strip()
    if expected_secret:
        if not webhook_secret or webhook_secret.strip() != expected_secret:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook secret",
            )

    accepted = enqueue_task(process_payment_webhook_event, payload or {})
    return {
        "accepted": bool(accepted),
        "message": "Webhook queued for async processing",
    }
