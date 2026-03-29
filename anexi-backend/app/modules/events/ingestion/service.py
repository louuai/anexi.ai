from sqlalchemy.orm import Session

from app.models import User
from app.modules.events.schemas import IngestionEnvelope, IngestionResponse
from app.modules.events.service import ingest_event


def ingest_from_source(
    db: Session,
    current_user: User,
    envelope: IngestionEnvelope,
) -> IngestionResponse:
    return ingest_event(db=db, current_user=current_user, envelope=envelope)

