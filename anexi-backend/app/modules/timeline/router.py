from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.modules.timeline.schemas import CustomerTimeline
from app.modules.timeline.service import build_customer_timeline
from app.routes.auth import get_current_user
from app.utils.tenant import require_tenant_id

router = APIRouter(tags=["Timeline"])


@router.get("/timeline/customers/{customer_id}", response_model=CustomerTimeline)
def get_customer_timeline(
    customer_id: str,
    merchant_id: int | None = None,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    limit: int = Query(default=1000, ge=1, le=5000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tenant_id = require_tenant_id(current_user.tenant_id)
    return build_customer_timeline(
        db=db,
        tenant_id=tenant_id,
        customer_id=customer_id,
        merchant_id=merchant_id,
        start_at=start_at,
        end_at=end_at,
        limit=limit,
    )

