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
