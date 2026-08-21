from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_access_routes_are_registered() -> None:
    source = _read("routes/__init__.py")
    for route in {
        "/access",
        "/access/checkout",
        "/access/payment/success",
        "/wallet-auth",
        "/wallet-auth/devices",
        "/wallet-auth/recovery",
        "/wallet-auth/step-up",
        "/lnurl/auth",
    }:
        assert f'PublicRouteSpec("{route}"' in source


def test_plan_codes_are_not_hard_coded_as_frontend_authority() -> None:
    source = _read("routes/access.py")
    for code in {
        "lite_pass",
        "basic_pass",
        "plus_pass",
        "pro_pass",
        "business_pass",
        "enterprise_pass",
    }:
        assert code not in source
    state = _read("state/access_acquisition_state.py")
    assert "get_access_offers_api_v1_access_offers_get" in state
    assert "adapt_access_offer" in state


def test_access_nav_replaces_legacy_auth_nav() -> None:
    source = _read("navigation.py")
    assert 'label="Access"' in source
    assert 'route="/access"' in source
    nav_section = source.split("PUBLIC_NAV_ITEMS", maxsplit=1)[1].split(
        "FOOTER_NAV_ITEMS", maxsplit=1
    )[0]
    assert "Login" not in nav_section
    assert "Register" not in nav_section
    assert "Sign in" not in nav_section
    assert "Sign up" not in nav_section


def test_access_pages_include_required_safety_copy() -> None:
    source = _read("components/auth/access.py") + _read("routes/wallet_auth.py")
    for line in (
        "Bastion will never ask for your Bitcoin seed or private key.",
        "This signature does not authorize a Bitcoin transaction.",
        "Use a dedicated Bastion authentication wallet or address.",
    ):
        assert line in source
    assert "Emergency Lockdown" in source


def test_no_active_password_or_bearer_form_in_access_ui() -> None:
    source = (_read("routes/access.py") + _read("routes/wallet_auth.py")).lower()
    assert "rx.input" not in source
    assert 'type="password"' not in source
    assert "authorization: bearer" not in source
    assert "/auth/login" not in source
    assert "/auth/register" not in source
