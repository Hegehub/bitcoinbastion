from app.db.models.audit import AuditLog
from app.db.repositories.audit_repository import AuditRepository


class SessionSpy:
    def __init__(self) -> None:
        self.called: list[str] = []

    def add(self, log: AuditLog) -> None:
        self.called.append("add")

    def commit(self) -> None:
        self.called.append("commit")

    def refresh(self, log: AuditLog) -> None:
        self.called.append("refresh")


class SessionCommitRaises(SessionSpy):
    def commit(self) -> None:
        super().commit()
        from sqlalchemy.exc import SQLAlchemyError

        raise SQLAlchemyError("db unavailable")


class NonSessionStub:
    pass


def _build_log() -> AuditLog:
    return AuditLog(
        actor_user_id=1,
        action="treasury.request.create",
        resource_type="treasury_request",
        resource_id="42",
        before_json="{}",
        after_json="{}",
    )


def test_record_persists_when_session_methods_exist() -> None:
    spy = SessionSpy()
    repo = AuditRepository(spy)  # type: ignore[arg-type]

    log = _build_log()
    result = repo.record(log)

    assert result is log
    assert spy.called == ["add", "commit", "refresh"]


def test_record_returns_log_when_db_is_non_session_stub() -> None:
    repo = AuditRepository(NonSessionStub())  # type: ignore[arg-type]

    log = _build_log()
    result = repo.record(log)

    assert result is log


def test_record_returns_log_when_session_raises_sqlalchemy_error() -> None:
    spy = SessionCommitRaises()
    repo = AuditRepository(spy)  # type: ignore[arg-type]

    log = _build_log()
    result = repo.record(log)

    assert result is log
    assert spy.called == ["add", "commit"]
