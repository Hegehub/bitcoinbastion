from typing import Any, cast

from app.services.wallet_auth.lnurl_recovery_factor import LNURLRecoveryRepository


def test_factor_receipt_is_created_once() -> None:
    repository = LNURLRecoveryRepository()
    receipt = cast(Any, object())
    assert repository.store_receipt_once("sha256:receipt", receipt) is True
    assert repository.store_receipt_once("sha256:receipt", receipt) is False
