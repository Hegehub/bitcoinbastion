from app.services.lnurl.merchant_address_policy import POLICY_ACTIONS, AllowMerchantAddressPolicy


def test_policy_actions_include_high_risk_management_hooks():
    assert "merchant_domain:create" in POLICY_ACTIONS
    assert "merchant_address:activate" in POLICY_ACTIONS
    assert "merchant_address:configure_payer_data" in POLICY_ACTIONS
    assert AllowMerchantAddressPolicy().evaluate("merchant_address:resolve", {}).allowed
