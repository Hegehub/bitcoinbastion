"""Integration test database bootstrap.

The integration API tests use the repository's configured SQLite test database
without running Alembic. Importing model metadata and creating missing tables
keeps these tests focused on route contracts instead of migration orchestration.
"""

from __future__ import annotations

import app.db.models  # noqa: F401 - ensure all SQLAlchemy models are registered
from app.db.base import Base
from app.db.session import engine


def pytest_configure() -> None:
    Base.metadata.create_all(bind=engine)
