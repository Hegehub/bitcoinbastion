from pathlib import Path


def test_required_readiness_docs_exist() -> None:
    required = [
        "docs/CALIBRATION_FRAMEWORK.md",
        "docs/EVIDENCE_VALIDATION.md",
        "docs/INDEX.md",
        "docs/STATUS.md",
        "docs/PRODUCTION_READINESS.md",
        "docs/ROADMAP.md",
        "docs/RELEASE_CANDIDATE_GATES.md",
        "docs/DEPLOYMENT_EVIDENCE_REGISTRY.md",
        "docs/RELEASE_CHECKLIST.md",
    ]
    for path in required:
        assert Path(path).exists()


def test_superseded_readiness_snapshots_are_archived() -> None:
    archive = Path("docs/archive/audits/2026")
    for name in (
        "STAGING_READINESS.md",
        "RC_STATUS_MATRIX.md",
        "PRE_RELEASE_GAPS.md",
        "PRODUCTION_TRANSITION_PACK.md",
    ):
        assert (archive / name).exists()


def test_no_false_production_calibration_claim() -> None:
    text = Path("docs/CALIBRATION_FRAMEWORK.md").read_text().lower()
    assert "production calibration evidence is still pending" in text
