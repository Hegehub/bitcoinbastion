from contextlib import contextmanager

from app.services.delivery.publish_service import PublishResult
from app.tasks.delivery_tasks import publish_signals_task


class _DummyTrackingService:
    def __init__(self, repo: object) -> None:
        self.repo = repo

    @contextmanager
    def track(self, task_name: str):
        yield


def test_publish_signals_task_returns_structured_publish_stats(monkeypatch) -> None:
    @contextmanager
    def _fake_session():
        yield object()

    monkeypatch.setattr("app.tasks.delivery_tasks.SessionLocal", _fake_session)
    monkeypatch.setattr("app.tasks.delivery_tasks.JobTrackingService", _DummyTrackingService)
    monkeypatch.setattr(
        "app.services.delivery.publish_service.SignalPublishService.publish_pending_with_stats",
        lambda self, limit=30: PublishResult(published=4, failed=1, skipped=2),
    )

    result = publish_signals_task.run()  # type: ignore[attr-defined]

    assert result == {"published": 4, "failed": 1, "skipped": 2}


def test_publish_signals_task_skips_duplicate_window(monkeypatch) -> None:
    from datetime import UTC, datetime

    class _Run:
        task_name = "delivery.publish"
        status = "started"
        started_at = datetime.now(UTC)

    class _TrackingWithRecent(_DummyTrackingService):
        def list_recent(self, limit: int = 10):
            return [_Run()]

    @contextmanager
    def _fake_session():
        yield object()

    monkeypatch.setattr("app.tasks.delivery_tasks.SessionLocal", _fake_session)
    monkeypatch.setattr("app.tasks.delivery_tasks.JobTrackingService", _TrackingWithRecent)

    result = publish_signals_task.run()  # type: ignore[attr-defined]

    assert result == {"status": "skipped", "reason": "duplicate_window_skip"}
