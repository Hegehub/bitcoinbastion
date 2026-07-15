from __future__ import annotations

from bastion_ui.services.settings import Settings


def test_settings_load_with_defaults() -> None:
    settings = Settings()

    assert settings.api_base_url == "http://localhost:8000"
    assert settings.public_site_mode is True
    assert settings.enable_trace is True
    assert settings.enable_market is True
    assert settings.enable_time_machine is True
    assert settings.enable_sovereign_grid is True
    assert settings.enable_console is True
    assert settings.request_timeout_seconds == 5
    assert settings.default_language == "en"
