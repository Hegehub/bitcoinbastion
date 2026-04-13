from app.core.exceptions import UnauthorizedError
from app.db.models.auth import User
from app.schemas.auth import LoginRequest, RegisterRequest
from app.services.auth.auth_service import AuthService


class FakeUserRepo:
    def __init__(self) -> None:
        self.users: dict[str, User] = {}

    def create(self, user: User) -> User:
        user.id = len(self.users) + 1
        self.users[user.username] = user
        return user

    def by_username(self, username: str) -> User | None:
        return self.users.get(username)


def test_register_and_login() -> None:
    repo = FakeUserRepo()
    service = AuthService(repo)  # type: ignore[arg-type]

    service.register(RegisterRequest(email="u@example.com", username="satoshi", password="password123"))
    token = service.login(LoginRequest(username="satoshi", password="password123"))
    assert token.access_token


def test_login_with_invalid_password_raises() -> None:
    repo = FakeUserRepo()
    service = AuthService(repo)  # type: ignore[arg-type]
    service.register(RegisterRequest(email="u@example.com", username="satoshi", password="password123"))

    try:
        service.login(LoginRequest(username="satoshi", password="bad-pass"))
        assert False, "Expected UnauthorizedError"
    except UnauthorizedError:
        assert True
