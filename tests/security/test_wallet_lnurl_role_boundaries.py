from app.services.access.policy_engine import BUSINESS_ROLE_SCOPES


def test_cashier_and_device_roles_are_bounded() -> None:
    cashier = BUSINESS_ROLE_SCOPES["cashier"]
    device = BUSINESS_ROLE_SCOPES["device"]
    assert "payregister:payment:create" in cashier
    assert "treasury:admin" not in cashier
    assert "business:owner:assign" not in cashier
    assert "create_api_key" not in device
