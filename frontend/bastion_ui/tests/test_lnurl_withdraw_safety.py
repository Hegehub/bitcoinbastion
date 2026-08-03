
from bastion_ui.state.lnurl_withdraw_state import LnurlWithdrawState


def test_withdraw_state_starts_without_qr_and_documents_policy_gate() -> None:
    state = LnurlWithdrawState()
    assert state.phase == "policy_check"
    assert state.display_lnurl == ""
    source = (
        __import__("pathlib")
        .Path(__file__)
        .resolve()
        .parents[1]
        .joinpath("state/lnurl_withdraw_state.py")
        .read_text()
    )
    assert 'result.get("policy_approved") is not True' in source
    assert 'self.display_lnurl = ""' in source
