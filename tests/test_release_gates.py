from pathlib import Path


def test_rc_gate_statuses_declared() -> None:
    text = Path("docs/RELEASE_CANDIDATE_GATES.md").read_text()
    for status in ("PASS", "FAIL", "PENDING", "NOT_EXECUTED"):
        assert status in text


def test_calibration_statuses_declared() -> None:
    text = Path("docs/CALIBRATION_FRAMEWORK.md").read_text()
    for status in (
        "NOT_IMPLEMENTED",
        "BASELINE",
        "PLACEHOLDER",
        "INTERNAL_ONLY",
        "STAGING_VALIDATED",
        "PRODUCTION_VALIDATED",
    ):
        assert status in text


def test_access_release_gate_target_declared() -> None:
    makefile = Path("Makefile").read_text()
    gate_doc = Path("docs/ACCESS_LAYER_RELEASE_GATE.md").read_text()

    assert "access-release-gate:" in makefile
    assert "tests/security/test_access_layer_release_gate.py" in makefile
    assert "make access-release-gate" in gate_doc


def test_wallet_lnurl_gate_is_required_and_truthful() -> None:
    makefile = Path("Makefile").read_text()
    workflow = Path(".github/workflows/ci.yml").read_text()
    script = Path("scripts/wallet-lnurl-auth-release-gate.sh")
    validation = Path("docs/WALLET_LNURL_AUTH_FINAL_VALIDATION.md").read_text()

    assert script.stat().st_mode & 0o111
    assert "wallet-lnurl-auth-release-gate:" in makefile
    assert "make wallet-lnurl-auth-release-gate" in workflow
    assert "--production" in script.read_text()
    assert "NOT PRODUCTION-READY" in validation
    assert "PQ-ready interfaces" in validation
