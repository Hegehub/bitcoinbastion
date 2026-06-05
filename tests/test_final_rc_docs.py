from pathlib import Path


def test_release_docs_exist() -> None:
    for p in (
        "CHANGELOG.md",
        "RELEASE_NOTES.md",
        "CONTRIBUTING.md",
        "SECURITY.md",
        "docs/FINAL_READINESS_MATRIX.md",
        "docs/RC_FREEZE.md",
        "docs/KNOWN_LIMITATIONS.md",
        "docs/SUPPORT_BOUNDARIES.md",
    ):
        assert Path(p).exists()


def test_forbidden_readiness_wording_absent() -> None:
    text = Path("README.md").read_text().lower() + Path("docs/PRODUCTION_READINESS.md").read_text().lower()
    assert "fully secure" not in text
    assert "enterprise certified" not in text


def test_final_production_audit_docs_exist_and_are_conservative() -> None:
    required = (
        Path("docs/FINAL_PRODUCTION_AUDIT.md"),
        Path("docs/SOVEREIGNTY_CERTIFICATION.md"),
        Path("docs/RELEASE_CANDIDATE_REPORT.md"),
    )
    for path in required:
        text = path.read_text()
        assert "Production Candidate" in text
        assert "Correlation is not proof of causation." in text
        assert "Not financial advice." in text
        assert "Evidence-based informational analysis." in text
        lowered = text.lower()
        assert "fully secure" not in lowered
        assert "bug free" not in lowered
        assert "guaranteed" not in lowered or "does not claim" in lowered


def test_release_candidate_report_declares_final_component_statuses() -> None:
    text = Path("docs/RELEASE_CANDIDATE_REPORT.md").read_text()
    for component in (
        "Backend Intelligence Core",
        "Evidence Layer",
        "Replay Layer",
        "Operator Governance",
        "Market Time Machine",
        "Website Integration",
        "Production Hardening",
    ):
        assert component in text
    assert "COMPLETE" in text
