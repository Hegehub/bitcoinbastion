from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import db_session
from app.db.repositories.user_repository import UserRepository
from app.schemas.user import UserOut

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserOut])
def list_users(limit: int = 20, offset: int = 0, db: Session = Depends(db_session)) -> list[UserOut]:
    users = UserRepository(db).list_users(limit=limit, offset=offset)
    return [UserOut.model_validate(user) for user in users]
