import asyncio
from pathlib import Path

from app.storage.object_store.client import DisabledObjectStore, ObjectStoreHealthCheck
from app.storage.object_store.local_store import LocalObjectStore


def test_object_store_health_check_returns_ok_for_local_backend(tmp_path: Path) -> None:
    check = ObjectStoreHealthCheck(
        LocalObjectStore(root=tmp_path),
        bucket="bastion-health",
        enabled=True,
    )
    result = asyncio.run(check.check_health())
    assert result.status == "ok"
    assert result.enabled is True
    assert result.degraded is False


def test_object_store_health_check_returns_disabled_for_disabled_backend() -> None:
    check = ObjectStoreHealthCheck(DisabledObjectStore(), bucket="unused", enabled=False)
    result = asyncio.run(check.check_health())
    assert result.status == "disabled"
    assert result.enabled is False
    assert result.degraded is False
