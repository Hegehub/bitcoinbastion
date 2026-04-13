from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.auth import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def by_username(self, username: str) -> User | None:
        stmt = select(User).where(User.username == username)
        return self.db.execute(stmt).scalar_one_or_none()

    def by_id(self, user_id: int) -> User | None:
        stmt = select(User).where(User.id == user_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_users(self, limit: int, offset: int) -> list[User]:
        stmt = select(User).order_by(User.id.desc()).limit(limit).offset(offset)
        return list(self.db.execute(stmt).scalars())

    def count(self) -> int:
        stmt = select(func.count()).select_from(User)
        return int(self.db.execute(stmt).scalar_one())
