from pathlib import Path


def test_required_readiness_docs_exist() -> None:
    required = [
        "docs/CALIBRATION_FRAMEWORK.md",
        "docs/EVIDENCE_VALIDATION.md",
        "docs/STAGING_READINESS.md",
        "docs/RELEASE_CANDIDATE_GATES.md",
        "docs/DEPLOYMENT_EVIDENCE_REGISTRY.md",
        "docs/RELEASE_CHECKLIST.md",
        "docs/RC_STATUS_MATRIX.md",
    ]
    for path in required:
        assert Path(path).exists()


def test_no_false_production_calibration_claim() -> None:
    text = Path("docs/CALIBRATION_FRAMEWORK.md").read_text().lower()
    assert "production calibration evidence is still pending" in text
