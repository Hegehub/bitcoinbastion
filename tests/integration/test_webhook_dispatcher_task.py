from dataclasses import dataclass

from app.tasks import outbox_tasks


@dataclass
class _Result:
    processed: int = 1
    delivered: int = 1
    retrying: int = 0
    dead: int = 0
    blocked: int = 0
    no_subscribers: int = 0


class _FakeDispatcher:
    def __init__(self, *args: object, **kwargs: object) -> None:
        pass

    def dispatch_pending_events(self, *, batch_size: int) -> _Result:
        assert batch_size == 7
        return _Result()


class _FakeSession:
    def __enter__(self) -> "_FakeSession":
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None


def test_dispatch_webhook_outbox_events_task_uses_dispatcher(monkeypatch) -> None:
    monkeypatch.setattr(outbox_tasks, "SessionLocal", lambda: _FakeSession())
    monkeypatch.setattr(outbox_tasks, "WebhookDispatcher", _FakeDispatcher)

    result = outbox_tasks.dispatch_webhook_outbox_events.run(batch_size=7)

    assert result == {
        "status": "ok",
        "processed": 1,
        "delivered": 1,
        "retrying": 0,
        "dead": 0,
        "blocked": 0,
        "no_subscribers": 0,
    }
