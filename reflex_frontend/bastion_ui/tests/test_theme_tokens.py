from __future__ import annotations

from bastion_ui.theme import responsive, tokens


def test_required_color_tokens_exist() -> None:
    for name in [
        "BITCOIN_ORANGE",
        "BASTION_BLACK",
        "BASTION_GRAPHITE",
        "BASTION_PANEL",
        "BASTION_PANEL_SOFT",
        "BASTION_BORDER",
        "BASTION_TEXT",
        "BASTION_TEXT_MUTED",
        "BASTION_TEXT_DIM",
        "BASTION_SUCCESS",
        "BASTION_WARNING",
        "BASTION_DANGER",
        "BASTION_INFO",
        "BASTION_NEUTRAL",
    ]:
        assert getattr(tokens, name).startswith("#")


def test_risk_evidence_and_breakpoint_tokens_exist() -> None:
    assert set(tokens.RISK_STATES) == {"low", "medium", "high", "unknown"}
    assert set(tokens.EVIDENCE_STATES) == {"strong", "partial", "weak", "unknown"}
    assert responsive.BREAKPOINTS["mobile"] == "0px"
    assert responsive.BREAKPOINTS["desktop"] == "1024px"
