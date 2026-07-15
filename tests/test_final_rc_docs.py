from pathlib import Path


def test_release_docs_exist() -> None:
    for p in (
        "CHANGELOG.md",
        "RELEASE_NOTES.md",
        "CONTRIBUTING.md",
        "SECURITY.md",
        "docs/INDEX.md",
        "docs/STATUS.md",
        "docs/PRODUCTION_READINESS.md",
        "docs/RC_FREEZE.md",
        "docs/KNOWN_LIMITATIONS.md",
        "docs/SUPPORT_BOUNDARIES.md",
    ):
        assert Path(p).exists()


def test_forbidden_readiness_wording_absent() -> None:
    text = (
        Path("README.md").read_text().lower()
        + Path("docs/PRODUCTION_READINESS.md").read_text().lower()
    )
    assert "fully secure" not in text
    assert "enterprise certified" not in text
    assert "99%" not in text
    assert "production candidate" not in text


def test_historical_production_audit_docs_are_archived_and_conservative() -> None:
    archive = Path("docs/archive/audits/2026")
    historical_claims = (
        archive / "FINAL_PRODUCTION_AUDIT.md",
        archive / "SOVEREIGNTY_CERTIFICATION.md",
        archive / "RELEASE_CANDIDATE_REPORT.md",
    )
    for path in historical_claims:
        text = path.read_text()
        assert "Production Candidate" in text
        assert "Correlation is not proof of causation." in text
        assert "Not financial advice." in text
        assert "Evidence-based informational analysis." in text
        lowered = text.lower()
        assert "fully secure" not in lowered
        assert "bug free" not in lowered
        assert "guaranteed" not in lowered or "does not claim" in lowered

    assert (archive / "FINAL_READINESS_MATRIX.md").exists()


def test_archived_release_candidate_report_preserves_component_statuses() -> None:
    text = Path("docs/archive/audits/2026/RELEASE_CANDIDATE_REPORT.md").read_text()
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


def test_current_status_overrides_historical_readiness_claims() -> None:
    status = Path("docs/STATUS.md").read_text()
    readiness = Path("docs/PRODUCTION_READINESS.md").read_text()

    assert "Not release-candidate and not production-ready" in status
    assert "Current decision: **NOT PRODUCTION-READY**" in readiness
    assert "docs/archive/" in status
