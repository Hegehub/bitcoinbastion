from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import db_session, get_current_user
from app.db.models.auth import User
from app.db.repositories.treasury_repository import TreasuryRepository
from app.schemas.base import PaginatedData, ResponseEnvelope
from app.schemas.treasury import TreasuryRequestIn, TreasuryRequestOut
from app.services.treasury.treasury_service import TreasuryService

router = APIRouter(prefix="/treasury", tags=["treasury"])


@router.post("/requests", response_model=ResponseEnvelope[TreasuryRequestOut])
def create_request(
    payload: TreasuryRequestIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(db_session),
) -> ResponseEnvelope[TreasuryRequestOut]:
    service = TreasuryService(TreasuryRepository(db))
    created = service.create_request(payload, requested_by=current_user.id)
    return ResponseEnvelope(data=TreasuryRequestOut.model_validate(created))


@router.get("/requests", response_model=ResponseEnvelope[PaginatedData[TreasuryRequestOut]])
def list_requests(
    limit: int = 20,
    offset: int = 0,
    status: str | None = None,
    _: User = Depends(get_current_user),
    db: Session = Depends(db_session),
) -> ResponseEnvelope[PaginatedData[TreasuryRequestOut]]:
    service = TreasuryService(TreasuryRepository(db))
    items = [
        TreasuryRequestOut.model_validate(item)
        for item in service.list_requests(limit=limit, offset=offset, status=status)
    ]
    total = service.count_requests(status=status)
    return ResponseEnvelope(data=PaginatedData(items=items, total=total, limit=limit, offset=offset))
