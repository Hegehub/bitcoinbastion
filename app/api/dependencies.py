from collections.abc import Generator

from fastapi import Depends, Header
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import UnauthorizedError
from app.db.models.auth import User
from app.db.repositories.user_repository import UserRepository
from app.db.session import get_db


def db_session() -> Generator[Session, None, None]:
    yield from get_db()


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(db_session),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedError()

    token = authorization.split(" ", 1)[1]
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise UnauthorizedError("Invalid access token") from exc

    user_id = payload.get("sub")
    if user_id is None:
        raise UnauthorizedError("Invalid token subject")

    repo = UserRepository(db)
    user = repo.by_id(int(user_id))
    if user is None:
        raise UnauthorizedError("User not found")
    return user
