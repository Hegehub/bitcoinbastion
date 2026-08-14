from __future__ import annotations

import pytest

from bastion_ui.security.generated_transport import (
    EphemeralBrowserPoPProvider,
    install_approved_browser_test_provider,
)
from bastion_ui.transport import foundation


def test_approved_bootstrap_installs_current_provider_protocol(monkeypatch) -> None:
    monkeypatch.setenv(
        "BASTION_GENERATED_TRANSPORT_SECURITY_PROFILE", "ephemeral-device-pop-v1"
    )
    monkeypatch.setenv("P9_TEST_SESSION_TOKEN", "sess_ephemeral")
    monkeypatch.setenv("P9_TEST_DEVICE_PRIVATE_KEY", "ephemeral-private-material")
    monkeypatch.setattr(foundation, "SECURITY_PROVIDER_FACTORY", None)
    assert install_approved_browser_test_provider() is True
    assert foundation.SECURITY_PROVIDER_FACTORY is EphemeralBrowserPoPProvider
    provider = foundation.SECURITY_PROVIDER_FACTORY()
    assert callable(provider.headers_for)


def test_bootstrap_is_inert_without_explicit_profile(monkeypatch) -> None:
    monkeypatch.delenv("BASTION_GENERATED_TRANSPORT_SECURITY_PROFILE", raising=False)
    monkeypatch.setattr(foundation, "SECURITY_PROVIDER_FACTORY", None)
    assert install_approved_browser_test_provider() is False
    assert foundation.SECURITY_PROVIDER_FACTORY is None


def test_bootstrap_rejects_incomplete_material(monkeypatch) -> None:
    monkeypatch.setenv(
        "BASTION_GENERATED_TRANSPORT_SECURITY_PROFILE", "ephemeral-device-pop-v1"
    )
    monkeypatch.delenv("P9_TEST_SESSION_TOKEN", raising=False)
    monkeypatch.delenv("P9_TEST_DEVICE_PRIVATE_KEY", raising=False)
    with pytest.raises(RuntimeError, match="incomplete"):
        install_approved_browser_test_provider()
