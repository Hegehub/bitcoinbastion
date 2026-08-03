import respx
from httpx import Response

from bastion_ui.lnurl_client import LnurlApiClient
from bastion_ui.wallet_auth_client import WalletAuthApiClient


@respx.mock
def test_wallet_client_matches_router_and_unwraps_envelope() -> None:
    route = respx.post("https://api.test/api/v1/wallet-auth/challenges").mock(
        return_value=Response(201, json={"data": {"challenge_id": "challenge"}, "error": None})
    )
    result = WalletAuthApiClient("https://api.test").create_challenge({"action": "login"})
    assert route.called
    assert result == {"challenge_id": "challenge"}


@respx.mock
def test_lnurl_verify_is_protocol_json_not_envelope() -> None:
    route = respx.get("https://api.test/v1/lnurl/pay/verify/pay_1").mock(
        return_value=Response(200, json={"settled": False, "status": "pending"})
    )
    result = LnurlApiClient("https://api.test").verify_payment("pay_1")
    assert route.called
    assert result["settled"] is False
