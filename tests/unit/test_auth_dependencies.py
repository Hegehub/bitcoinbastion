import pytest

from app.api.dependencies import decode_user_id_from_token, get_current_user
from app.core.exceptions import AppError, UnauthorizedError


def test_decode_user_id_from_token_rejects_legacy_jwt() -> None:
    with pytest.raises(AppError) as exc_info:
        decode_user_id_from_token("legacy.jwt.token")

    assert exc_info.value.code == "access_legacy_bearer_rejected"
    assert exc_info.value.status_code == 401


def test_get_current_user_rejects_authorization_bearer() -> None:
    with pytest.raises(AppError) as exc_info:
        get_current_user(authorization="Bearer legacy.jwt.token", db=None)  # type: ignore[arg-type]

    assert exc_info.value.code == "access_legacy_bearer_rejected"


def test_get_current_user_without_access_headers_requires_proof_of_access() -> None:
    with pytest.raises(UnauthorizedError):
        get_current_user(authorization=None, db=None)  # type: ignore[arg-type]
