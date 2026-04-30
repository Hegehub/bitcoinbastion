import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.base import Base
from app.db.models.delivery import DeliveryLog
from app.db.models.signal import Signal
from app.db.repositories.delivery_repository import DeliveryRepository
from app.db.repositories.signal_repository import SignalRepository
from app.services.delivery.publish_service import PublishResult, SignalPublishService
from app.services.delivery.telegram_delivery import TelegramDeliveryError, TelegramSendResult


def _build_signal(title: str, score: float) -> Signal:
    return Signal(
        signal_type="news",
        severity="high",
        score=score,
        confidence=0.85,
        title=title,
        summary="Signal summary",
    )


class StubTelegramClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def send_message(self, *, destination: str, message: str) -> TelegramSendResult:
        self.calls.append((destination, message))
        return TelegramSendResult(destination=destination, message_id="12345")


class FailingTelegramClient:
    def send_message(self, *, destination: str, message: str) -> TelegramSendResult:
        raise TelegramDeliveryError("provider timeout")


class BrokenTelegramClient:
    def send_message(self, *, destination: str, message: str) -> TelegramSendResult:
        raise ValueError("serialization bug")


class FlakyTelegramClient:
    def __init__(self) -> None:
        self.calls = 0

    def send_message(self, *, destination: str, message: str) -> TelegramSendResult:
        self.calls += 1
        if self.calls == 1:
            raise ValueError("first call decode issue")
        return TelegramSendResult(destination=destination, message_id=f"m{self.calls}")


class DualFailureTelegramClient:
    def __init__(self) -> None:
        self.calls = 0

    def send_message(self, *, destination: str, message: str) -> TelegramSendResult:
        self.calls += 1
        if self.calls == 1:
            raise TelegramDeliveryError("provider timeout")
        raise ValueError("unexpected serializer failure")


def _configure_settings(*, destination: str = "@alerts", bot_token: str = "test-token") -> None:
    get_settings.cache_clear()
    settings = get_settings()
    settings.telegram_default_chat_id = destination
    settings.telegram_bot_token = bot_token


def test_publish_service_marks_unpublished_signals_as_published(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure_settings()
    events: list[dict[str, str]] = []
    monkeypatch.setattr(
        "app.services.delivery.publish_service.increment_delivery_publish_event",
        lambda **kwargs: events.append(kwargs),
    )
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        signal_repo = SignalRepository(db)
        signal_repo.add(_build_signal("First", 0.9))
        signal_repo.add(_build_signal("Second", 0.8))
        telegram_client = StubTelegramClient()

        published = SignalPublishService(
            signals=signal_repo,
            deliveries=DeliveryRepository(db),
            telegram_client=telegram_client,
        ).publish_pending(limit=10)

        remaining = signal_repo.unpublished(limit=10)

    assert published == 2
    assert remaining == []
    assert len(telegram_client.calls) == 2
    assert events == [{"status": "sent"}, {"status": "sent"}]


def test_publish_service_with_stats_reports_counters(monkeypatch: pytest.MonkeyPatch) -> None:
    _configure_settings()
    events: list[dict[str, str]] = []
    monkeypatch.setattr(
        "app.services.delivery.publish_service.increment_delivery_publish_event",
        lambda **kwargs: events.append(kwargs),
    )
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        signal_repo = SignalRepository(db)
        first = signal_repo.add(_build_signal("First", 0.9))
        signal_repo.add(_build_signal("Second", 0.8))
        delivery_repo = DeliveryRepository(db)

        service = SignalPublishService(
            signals=signal_repo,
            deliveries=delivery_repo,
            telegram_client=StubTelegramClient(),
        )
        first_result = service.publish_pending_with_stats(limit=10)

        first.is_published = False
        db.commit()
        second_result = service.publish_pending_with_stats(limit=10)

    assert first_result.published == 2
    assert first_result.failed == 0
    assert first_result.skipped == 0
    assert second_result.published == 0
    assert second_result.failed == 0
    assert second_result.skipped == 1
    assert events == [
        {"status": "sent"},
        {"status": "sent"},
        {"status": "skipped", "reason": "duplicate_already_sent"},
    ]


def test_publish_service_suppresses_duplicates_for_same_destination(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure_settings()
    events: list[dict[str, str]] = []
    monkeypatch.setattr(
        "app.services.delivery.publish_service.increment_delivery_publish_event",
        lambda **kwargs: events.append(kwargs),
    )
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        signal_repo = SignalRepository(db)
        signal = signal_repo.add(_build_signal("Duplicate candidate", 0.9))
        delivery_repo = DeliveryRepository(db)
        telegram_client = StubTelegramClient()

        service = SignalPublishService(
            signals=signal_repo,
            deliveries=delivery_repo,
            telegram_client=telegram_client,
        )
        first_count = service.publish_pending(limit=10)

        # Force unpublished flag back to emulate a rerun race/rollback scenario.
        signal.is_published = False
        db.commit()

        second_count = service.publish_pending(limit=10)

    assert first_count == 1
    assert second_count == 0
    assert len(telegram_client.calls) == 1
    assert events == [
        {"status": "sent"},
        {"status": "skipped", "reason": "duplicate_already_sent"},
    ]


def test_publish_service_records_failure_and_keeps_signal_unpublished(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure_settings()
    events: list[dict[str, str]] = []
    monkeypatch.setattr(
        "app.services.delivery.publish_service.increment_delivery_publish_event",
        lambda **kwargs: events.append(kwargs),
    )
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        signal_repo = SignalRepository(db)
        signal = signal_repo.add(_build_signal("Unsent signal", 0.95))
        delivery_repo = DeliveryRepository(db)

        published = SignalPublishService(
            signals=signal_repo,
            deliveries=delivery_repo,
            telegram_client=FailingTelegramClient(),
        ).publish_pending(limit=10)

        stored_signal = signal_repo.get(signal.id)
        failure_logs = db.query(DeliveryLog).filter(DeliveryLog.signal_id == signal.id).all()

    assert published == 0
    assert stored_signal is not None
    assert stored_signal.is_published is False
    assert len(failure_logs) == 1
    assert failure_logs[0].delivery_status == "failed"
    assert events == [{"status": "failed", "reason": "telegram_delivery_error"}]


def test_publish_service_returns_zero_when_destination_not_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure_settings(destination="")
    events: list[dict[str, str]] = []
    monkeypatch.setattr(
        "app.services.delivery.publish_service.increment_delivery_publish_event",
        lambda **kwargs: events.append(kwargs),
    )
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        signal_repo = SignalRepository(db)
        signal_repo.add(_build_signal("No destination", 0.88))

        published = SignalPublishService(
            signals=signal_repo,
            deliveries=DeliveryRepository(db),
            telegram_client=StubTelegramClient(),
        ).publish_pending(limit=10)

        remaining = signal_repo.unpublished(limit=10)

    assert published == 0
    assert len(remaining) == 1
    assert events == [{"status": "skipped", "reason": "missing_destination"}]


def test_publish_service_with_stats_skips_all_when_config_missing() -> None:
    _configure_settings(destination="")
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        signal_repo = SignalRepository(db)
        signal_repo.add(_build_signal("No destination 1", 0.88))
        signal_repo.add(_build_signal("No destination 2", 0.87))

        result = SignalPublishService(
            signals=signal_repo,
            deliveries=DeliveryRepository(db),
            telegram_client=StubTelegramClient(),
        ).publish_pending_with_stats(limit=10)

    assert result.published == 0
    assert result.failed == 0
    assert result.skipped == 2


def test_publish_service_returns_zero_when_bot_token_not_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure_settings(bot_token="")
    events: list[dict[str, str]] = []
    monkeypatch.setattr(
        "app.services.delivery.publish_service.increment_delivery_publish_event",
        lambda **kwargs: events.append(kwargs),
    )
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        signal_repo = SignalRepository(db)
        signal_repo.add(_build_signal("No bot token", 0.88))

        published = SignalPublishService(
            signals=signal_repo,
            deliveries=DeliveryRepository(db),
            telegram_client=StubTelegramClient(),
        ).publish_pending(limit=10)

        remaining = signal_repo.unpublished(limit=10)

    assert published == 0
    assert len(remaining) == 1
    assert events == [{"status": "skipped", "reason": "missing_bot_token"}]


def test_publish_service_records_unexpected_exception_as_failed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure_settings()
    events: list[dict[str, str]] = []
    monkeypatch.setattr(
        "app.services.delivery.publish_service.increment_delivery_publish_event",
        lambda **kwargs: events.append(kwargs),
    )
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        signal_repo = SignalRepository(db)
        signal = signal_repo.add(_build_signal("Unexpected failure", 0.91))
        delivery_repo = DeliveryRepository(db)

        published = SignalPublishService(
            signals=signal_repo,
            deliveries=delivery_repo,
            telegram_client=BrokenTelegramClient(),
        ).publish_pending(limit=10)

        stored_signal = signal_repo.get(signal.id)
        failure_logs = db.query(DeliveryLog).filter(DeliveryLog.signal_id == signal.id).all()

    assert published == 0
    assert stored_signal is not None
    assert stored_signal.is_published is False
    assert len(failure_logs) == 1
    assert failure_logs[0].delivery_status == "failed"
    assert "unexpected_error" in failure_logs[0].error_message
    assert events == [{"status": "failed", "reason": "unexpected_exception"}]


def test_publish_service_continues_after_unexpected_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure_settings()
    events: list[dict[str, str]] = []
    monkeypatch.setattr(
        "app.services.delivery.publish_service.increment_delivery_publish_event",
        lambda **kwargs: events.append(kwargs),
    )
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        signal_repo = SignalRepository(db)
        first = signal_repo.add(_build_signal("First flaky", 0.93))
        second = signal_repo.add(_build_signal("Second should send", 0.92))
        delivery_repo = DeliveryRepository(db)

        published = SignalPublishService(
            signals=signal_repo,
            deliveries=delivery_repo,
            telegram_client=FlakyTelegramClient(),
        ).publish_pending(limit=10)

        first_signal = signal_repo.get(first.id)
        second_signal = signal_repo.get(second.id)
        failure_logs = db.query(DeliveryLog).filter(DeliveryLog.signal_id == first.id).all()

    assert published == 1
    assert first_signal is not None and first_signal.is_published is False
    assert second_signal is not None and second_signal.is_published is True
    assert len(failure_logs) == 1
    assert events == [
        {"status": "failed", "reason": "unexpected_exception"},
        {"status": "sent"},
    ]


def test_publish_service_with_stats_counts_known_and_unexpected_failures() -> None:
    _configure_settings()
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        signal_repo = SignalRepository(db)
        signal_repo.add(_build_signal("Known failure", 0.94))
        signal_repo.add(_build_signal("Unexpected failure", 0.93))
        delivery_repo = DeliveryRepository(db)

        result = SignalPublishService(
            signals=signal_repo,
            deliveries=delivery_repo,
            telegram_client=DualFailureTelegramClient(),
        ).publish_pending_with_stats(limit=10)

        remaining = signal_repo.unpublished(limit=10)

    assert result.published == 0
    assert result.failed == 2
    assert result.skipped == 0
    assert len(remaining) == 2


def test_publish_pending_backward_compatible_return_value(monkeypatch: pytest.MonkeyPatch) -> None:
    _configure_settings()
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        service = SignalPublishService(
            signals=SignalRepository(db),
            deliveries=DeliveryRepository(db),
            telegram_client=StubTelegramClient(),
        )
        monkeypatch.setattr(
            service,
            "publish_pending_with_stats",
            lambda limit=20: PublishResult(published=7, failed=3, skipped=2),
        )

        published = service.publish_pending(limit=20)

    assert published == 7


def test_publish_service_skips_when_retry_limit_reached(monkeypatch: pytest.MonkeyPatch) -> None:
    _configure_settings()
    settings = get_settings()
    settings.delivery_max_failed_attempts_per_signal_destination = 2
    settings.delivery_retry_cooldown_seconds = 0

    events: list[dict[str, str]] = []
    monkeypatch.setattr(
        "app.services.delivery.publish_service.increment_delivery_publish_event",
        lambda **kwargs: events.append(kwargs),
    )

    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        signal_repo = SignalRepository(db)
        signal = signal_repo.add(_build_signal("Retry limited", 0.9))
        delivery_repo = DeliveryRepository(db)
        delivery_repo.record_failed(
            signal_id=signal.id,
            destination="@alerts",
            payload_snapshot={"title": "x"},
            error_message="first",
        )
        delivery_repo.record_failed(
            signal_id=signal.id,
            destination="@alerts",
            payload_snapshot={"title": "x"},
            error_message="second",
        )

        result = SignalPublishService(
            signals=signal_repo,
            deliveries=delivery_repo,
            telegram_client=StubTelegramClient(),
        ).publish_pending_with_stats(limit=10)

        stored_signal = signal_repo.get(signal.id)

    assert result.published == 0
    assert result.failed == 0
    assert result.skipped == 1
    assert stored_signal is not None and stored_signal.is_published is False
    assert events == [{"status": "skipped", "reason": "retry_limit_exceeded"}]


def test_publish_service_skips_when_retry_cooldown_active(monkeypatch: pytest.MonkeyPatch) -> None:
    _configure_settings()
    settings = get_settings()
    settings.delivery_max_failed_attempts_per_signal_destination = 5
    settings.delivery_retry_cooldown_seconds = 3600

    events: list[dict[str, str]] = []
    monkeypatch.setattr(
        "app.services.delivery.publish_service.increment_delivery_publish_event",
        lambda **kwargs: events.append(kwargs),
    )

    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        signal_repo = SignalRepository(db)
        signal = signal_repo.add(_build_signal("Cooldown signal", 0.89))
        delivery_repo = DeliveryRepository(db)
        delivery_repo.record_failed(
            signal_id=signal.id,
            destination="@alerts",
            payload_snapshot={"title": "y"},
            error_message="transient",
        )

        result = SignalPublishService(
            signals=signal_repo,
            deliveries=delivery_repo,
            telegram_client=StubTelegramClient(),
        ).publish_pending_with_stats(limit=10)

        stored_signal = signal_repo.get(signal.id)

    assert result.published == 0
    assert result.failed == 0
    assert result.skipped == 1
    assert stored_signal is not None and stored_signal.is_published is False
    assert events == [{"status": "skipped", "reason": "retry_cooldown_active"}]
