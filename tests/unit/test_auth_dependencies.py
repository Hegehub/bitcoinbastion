from app.api.dependencies import decode_user_id_from_token
from app.core.config import get_settings
from app.core.exceptions import UnauthorizedError
from jose import jwt


def test_decode_user_id_from_token_success() -> None:
    settings = get_settings()
    token = jwt.encode({"sub": "42"}, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    assert decode_user_id_from_token(token) == 42


def test_decode_user_id_from_token_invalid_subject() -> None:
    settings = get_settings()
    token = jwt.encode({"sub": "bad"}, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    try:
        decode_user_id_from_token(token)
        assert False, "Expected UnauthorizedError"
    except UnauthorizedError:
        assert True
