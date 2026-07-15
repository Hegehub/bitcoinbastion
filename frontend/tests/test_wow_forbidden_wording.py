from __future__ import annotations

from pathlib import Path

from bastion_ui.security.visual_safety import contains_forbidden_wording, sanitize_visual_label

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = (
    "clean address",
    "dirty address",
    "criminal address",
    "guaranteed safe",
    "approved payment",
    "verified illicit",
)


def test_visual_safety_detects_forbidden_terms() -> None:
    for term in FORBIDDEN:
        assert contains_forbidden_wording(term)
        assert term not in sanitize_visual_label(term).lower()


def test_wow_components_do_not_use_forbidden_wording() -> None:
    text = "\n".join(
        path.read_text(encoding="utf-8").lower()
        for path in (ROOT / "bastion_ui/components/wow").glob("*.py")
    )
    for term in FORBIDDEN:
        assert term not in text
    assert "rx.input" not in text
    assert 'type="file"' not in text
