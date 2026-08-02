from app.api import access_dependencies as deps
from app.api import wallet_auth_dependencies as wallet_deps


def test_protected_dependencies_have_runtime_classification_markers() -> None:
    assert deps.require_access_session.__bastion_route_classification__ == "protected"
    assert wallet_deps.require_wallet_policy.__bastion_route_classification__ == "protected"
    assert wallet_deps.require_fresh_wallet_step_up.__bastion_route_classification__ == "high_risk"
