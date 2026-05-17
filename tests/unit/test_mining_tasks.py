from contextlib import contextmanager

from app.tasks.mining_tasks import refresh_stratum_v2_capabilities


def test_refresh_stratum_v2_capabilities_returns_structured_summary(monkeypatch) -> None:
    class _FakeService:
        def __init__(self, *_args, **_kwargs) -> None:
            self.calls = 0

        def upsert_pool_capability_metadata(self, _item):
            self.calls += 1
            if self.calls == 1:
                return {"endpoint_count": 0}
            return {"endpoint_count": 1}

    @contextmanager
    def _fake_session():
        yield object()

    monkeypatch.setattr("app.tasks.mining_tasks.SessionLocal", _fake_session)
    monkeypatch.setattr("app.tasks.mining_tasks.MiningPoolRegistryService", _FakeService)

    result = refresh_stratum_v2_capabilities.run()  # type: ignore[attr-defined]
    assert result["processed"] == 2
    assert result["created"] == 1
    assert result["updated"] == 1
    assert result["failed"] == 0
    assert isinstance(result["warnings"], list)


def test_refresh_stratum_v2_capabilities_continues_on_failure(monkeypatch) -> None:
    class _FakeService:
        def __init__(self, *_args, **_kwargs) -> None:
            self.calls = 0

        def upsert_pool_capability_metadata(self, _item):
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("boom")
            return {"endpoint_count": 0}

    @contextmanager
    def _fake_session():
        yield object()

    monkeypatch.setattr("app.tasks.mining_tasks.SessionLocal", _fake_session)
    monkeypatch.setattr("app.tasks.mining_tasks.MiningPoolRegistryService", _FakeService)

    result = refresh_stratum_v2_capabilities.run()  # type: ignore[attr-defined]
    assert result["processed"] == 2
    assert result["failed"] == 1
    assert result["created"] == 1
    assert len(result["warnings"]) >= 1
