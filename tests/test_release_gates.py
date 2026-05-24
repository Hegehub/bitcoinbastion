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
