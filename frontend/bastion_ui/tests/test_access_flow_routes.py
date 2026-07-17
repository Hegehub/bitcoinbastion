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
        "/access/success",
        "/access/import",
        "/access/me",
        "/access/recovery",
        "/access/lockdown",
    }:
        assert f'PublicRouteSpec("{route}"' in source


def test_plan_codes_match_backend_contract() -> None:
    source = _read("routes/access.py")
    for code in {
        "lite_pass",
        "basic_pass",
        "plus_pass",
        "pro_pass",
        "business_pass",
        "enterprise_pass",
    }:
        assert code in source


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
    source = _read("routes/access.py")
    for line in (
        "This is not a password.",
        "This is not your Bitcoin wallet seed.",
        "Bastion will never ask for your Bitcoin wallet seed or private key.",
    ):
        assert line in source
    assert "Save this Bastion Access Pass now. It will be shown only once." in source
    assert "Development signer — not for production" in source
    assert "Lockdown is designed for suspected compromise" in source


def test_no_active_password_or_bearer_form_in_access_ui() -> None:
    source = _read("routes/access.py").lower()
    assert "rx.input" not in source
    assert 'type="password"' not in source
    assert "authorization: bearer" not in source
    assert "/auth/login" not in source
    assert "/auth/register" not in source
