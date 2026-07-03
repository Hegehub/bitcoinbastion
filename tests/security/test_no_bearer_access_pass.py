from __future__ import annotations

from pathlib import Path

from app.domain.access.plans import PlanCode
from app.services.access.pass_generator import generate_raw_access_pass


def test_raw_access_pass_is_not_bearer_authorization_material() -> None:
    raw_pass = generate_raw_access_pass(PlanCode.LITE)
    authorization_header = f"Authorization: Bearer {raw_pass}"

    assert raw_pass.startswith("bbp_live_")
    assert "Bearer" in authorization_header
    assert "Authorization" not in Path("app/services/access/certificate_issuer.py").read_text()
    assert "Authorization" not in Path("app/services/access/pass_generator.py").read_text()


def test_raw_access_pass_is_not_accepted_directly_as_session() -> None:
    raw_pass = generate_raw_access_pass(PlanCode.PRO)

    assert raw_pass.startswith("bbp_live_")
    assert "session" not in Path("app/services/access/pass_generator.py").read_text().lower()


def test_certificate_alone_does_not_authenticate_protected_endpoint() -> None:
    issuer_source = Path("app/services/access/certificate_issuer.py").read_text().lower()

    assert "def authenticate" not in issuer_source
    assert "current_user" not in issuer_source
    assert "bearer" not in issuer_source
