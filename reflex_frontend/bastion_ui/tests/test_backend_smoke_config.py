from __future__ import annotations

import pytest

from bastion_ui.config import AppConfig


def test_backend_smoke_environment_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BB_API_BASE_URL", "http://api:8000")
    monkeypatch.setenv("BB_REQUEST_TIMEOUT_SECONDS", "7")
    monkeypatch.setenv("BB_ENABLE_TRACE", "true")
    monkeypatch.setenv("BB_ENABLE_CONSOLE", "true")
    monkeypatch.setenv("BB_ENABLE_TIME_MACHINE", "true")

    config = AppConfig()

    assert config.api_base_url == "http://api:8000"
    assert config.request_timeout_seconds == 7
    assert config.enable_trace is True
    assert config.enable_console is True
    assert config.enable_time_machine is True
