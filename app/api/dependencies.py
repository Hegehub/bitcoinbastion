from collections.abc import Generator
from typing import NoReturn

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.core.exceptions import AppError, UnauthorizedError
from app.db.models.auth import User
from app.db.session import get_db

LEGACY_BEARER_REJECTED_MESSAGE = (
    "Proof-of-Access requires Bastion access headers, not Authorization Bearer."
)


def db_session() -> Generator[Session, None, None]:
    yield from get_db()


def _access_session_required() -> NoReturn:
    raise UnauthorizedError("Proof-of-Access session headers are required for protected APIs.")


def _legacy_bearer_rejected() -> NoReturn:
    raise AppError(
        message=LEGACY_BEARER_REJECTED_MESSAGE,
        status_code=401,
        code="access_legacy_bearer_rejected",
    )


def decode_user_id_from_token(token: str) -> NoReturn:
    """Fail closed: JWT/bearer tokens are no longer authentication credentials."""
    _legacy_bearer_rejected()


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(db_session),
) -> User:
    """Disabled legacy dependency retained only to reject old protected paths."""
    _ = db
    if authorization and authorization.lower().startswith("bearer "):
        _legacy_bearer_rejected()
    _access_session_required()


def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Disabled legacy admin dependency retained only to fail closed."""
    _ = current_user
    _access_session_required()
