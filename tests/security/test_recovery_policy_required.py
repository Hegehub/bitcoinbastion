import inspect
from app.services.wallet_auth.recovery.capsule import RecoveryCapsuleService


def test_policy_authorizer_is_required_constructor_dependency() -> None:
    parameter = inspect.signature(RecoveryCapsuleService).parameters["policy_authorizer"]
    assert parameter.default is inspect.Parameter.empty
