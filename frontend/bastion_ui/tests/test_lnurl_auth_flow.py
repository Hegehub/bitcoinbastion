from pathlib import Path

from bastion_ui.auth_models import AuthFlowState
from bastion_ui.components.auth.access import lnurl_auth_qr_code
from bastion_ui.lnurl_client import LnurlApiClient


def test_lnurl_auth_states_and_accessible_qr() -> None:
    assert {item.value for item in AuthFlowState} >= {
        "generating",
        "waiting_for_wallet",
        "verifying",
        "wallet_verified",
        "binding_device",
        "creating_session",
        "authenticated",
        "expired",
        "rejected",
        "unsupported_wallet",
        "error",
    }
    rendered = str(lnurl_auth_qr_code("lnurl1publicchallenge"))
    assert "LNURL authentication QR code" in rendered
    assert "Open in Lightning wallet" in rendered
    assert "Expires" in rendered


def test_frontend_does_not_fake_missing_auth_status_contract() -> None:
    assert LnurlApiClient.auth_status_supported() is False
    source = (Path(__file__).resolve().parents[1] / "routes/lnurl.py").read_text()
    assert "does not expose an auth-attempt status route" in source
