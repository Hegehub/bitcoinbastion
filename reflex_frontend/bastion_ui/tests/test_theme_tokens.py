from __future__ import annotations

from bastion_ui.theme import responsive, tokens


def test_required_color_tokens_exist() -> None:
    for name in (
        "BITCOIN_ORANGE",
        "BASTION_BLACK",
        "BASTION_GRAPHITE",
        "BASTION_PANEL",
        "BASTION_PANEL_SOFT",
        "BASTION_BORDER",
        "BASTION_TEXT",
        "BASTION_TEXT_MUTED",
        "BASTION_TEXT_DIM",
    ):
        assert getattr(tokens, name)


def test_risk_and_evidence_tokens_exist() -> None:
    for name in ("RISK_LOW", "RISK_MEDIUM", "RISK_HIGH", "RISK_UNKNOWN"):
        assert getattr(tokens, name)
    for name in ("EVIDENCE_STRONG", "EVIDENCE_PARTIAL", "EVIDENCE_WEAK", "EVIDENCE_UNKNOWN"):
        assert getattr(tokens, name)


def test_breakpoint_tokens_exist() -> None:
    assert responsive.BREAKPOINTS == {
        "mobile": "0px",
        "tablet": "768px",
        "desktop": "1024px",
        "wide": "1280px",
    }
