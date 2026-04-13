from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import db_session, get_current_user
from app.db.models.auth import User
from app.schemas.base import ResponseEnvelope
from app.schemas.treasury import TreasuryRequestIn, TreasuryRequestOut
from app.services.treasury.treasury_service import TreasuryService

router = APIRouter(prefix="/treasury", tags=["treasury"])


@router.post("/requests", response_model=ResponseEnvelope[TreasuryRequestOut])
def create_request(
    payload: TreasuryRequestIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(db_session),
) -> ResponseEnvelope[TreasuryRequestOut]:
    created = TreasuryService(db).create_request(payload, requested_by=current_user.id)
    return ResponseEnvelope(data=TreasuryRequestOut.model_validate(created))
