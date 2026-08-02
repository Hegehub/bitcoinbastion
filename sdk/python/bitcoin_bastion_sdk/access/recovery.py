from __future__ import annotations

from typing import Any

from bitcoin_bastion_sdk.safety import assert_safe


class RecoveryClient:
    def __init__(self, wallet: Any) -> None:
        self._wallet = wallet

    def start_recovery(self, **payload: Any) -> Any:
        assert_safe(payload)
        return self._wallet.start_recovery(**payload)

    def get_recovery_status(self, recovery_id: str) -> Any:
        return self._wallet.recovery_status(recovery_id)

    def submit_recovery_factor(self, recovery_id: str, **payload: Any) -> Any:
        assert_safe(payload)
        return self._wallet.submit_recovery_factor(recovery_id, **payload)

    def complete_recovery(self, recovery_id: str, **payload: Any) -> Any:
        assert_safe(payload)
        return self._wallet.complete_recovery(recovery_id, **payload)
