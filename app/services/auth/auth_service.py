from app.core.exceptions import UnauthorizedError
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models.auth import User
from app.db.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse


class AuthService:
    def __init__(self, repo: UserRepository) -> None:
        self.repo = repo

    def register(self, payload: RegisterRequest) -> User:
        user = User(
            email=payload.email,
            username=payload.username,
            hashed_password=hash_password(payload.password),
        )
        return self.repo.create(user)

    def login(self, payload: LoginRequest) -> TokenResponse:
        user = self.repo.by_username(payload.username)
        if user is None or not verify_password(payload.password, user.hashed_password):
            raise UnauthorizedError("Invalid username or password")

        token = create_access_token(subject=str(user.id))
        return TokenResponse(access_token=token)
