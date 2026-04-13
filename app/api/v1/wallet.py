from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import db_session, get_current_user
from app.db.models.auth import User
from app.db.repositories.wallet_repository import WalletRepository
from app.schemas.base import PaginatedData, ResponseEnvelope
from app.schemas.wallet import WalletHealthRequest, WalletHealthResponse, WalletProfileOut
from app.services.wallet.health_service import WalletHealthService

router = APIRouter(prefix="/wallet", tags=["wallet"])


@router.post("/health", response_model=ResponseEnvelope[WalletHealthResponse])
def wallet_health(payload: WalletHealthRequest) -> ResponseEnvelope[WalletHealthResponse]:
    result = WalletHealthService().evaluate(payload)
    return ResponseEnvelope(data=result)


@router.get("/profiles", response_model=ResponseEnvelope[PaginatedData[WalletProfileOut]])
def list_profiles(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(db_session),
) -> ResponseEnvelope[PaginatedData[WalletProfileOut]]:
    repo = WalletRepository(db)
    items = [
        WalletProfileOut.model_validate(item)
        for item in repo.list_by_user(user_id=current_user.id, limit=limit, offset=offset)
    ]
    total = repo.count_by_user(current_user.id)
    return ResponseEnvelope(data=PaginatedData(items=items, total=total, limit=limit, offset=offset))
