import inspect
from app.services.wallet_auth.recovery.capsule import RecoveryCapsuleService


def test_revocation_resolver_and_artifact_manager_are_required() -> None:
    parameters = inspect.signature(RecoveryCapsuleService).parameters
    assert parameters["revocation_resolver"].default is inspect.Parameter.empty
    assert parameters["artifact_manager"].default is inspect.Parameter.empty
