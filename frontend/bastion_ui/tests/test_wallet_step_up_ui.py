from pathlib import Path


def test_step_up_displays_human_intent_and_does_not_auto_retry() -> None:
    text = Path(__file__).resolve().parents[1].joinpath("routes/wallet_auth.py").read_text()
    for value in (
        "requested scopes",
        "cannot_access",
        "risk",
        "Fresh Bitcoin proof",
        "fresh LNURL-auth",
    ):
        assert value in text
    assert "not automatically retried" in text
