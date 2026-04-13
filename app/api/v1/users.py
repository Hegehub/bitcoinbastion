from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import db_session, get_current_user
from app.db.models.auth import User
from app.db.repositories.user_repository import UserRepository
from app.schemas.base import PaginatedData, ResponseEnvelope
from app.schemas.user import UserOut

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=ResponseEnvelope[PaginatedData[UserOut]])
def list_users(
    limit: int = 20,
    offset: int = 0,
    _: User = Depends(get_current_user),
    db: Session = Depends(db_session),
) -> ResponseEnvelope[PaginatedData[UserOut]]:
    repo = UserRepository(db)
    users = repo.list_users(limit=limit, offset=offset)
    total = repo.count()
    return ResponseEnvelope(
        data=PaginatedData(items=[UserOut.model_validate(user) for user in users], total=total, limit=limit, offset=offset)
    )


@router.get("/me", response_model=ResponseEnvelope[UserOut])
def me(current_user: User = Depends(get_current_user)) -> ResponseEnvelope[UserOut]:
    return ResponseEnvelope(data=UserOut.model_validate(current_user))
