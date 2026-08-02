from typing import Any


class LockdownClient:
    def __init__(self, wallet: Any) -> None:
        self._wallet = wallet

    def start_lockdown(self, **payload: Any) -> Any:
        return self._wallet.start_lockdown(**payload)

    def get_lockdown_status(self, recovery_reference: str | None = None) -> Any:
        params = {"recovery_reference": recovery_reference} if recovery_reference else None
        return self._wallet._transport.request("GET", "/wallet-auth/lockdown/status", params=params)

    def request_lockdown_release(self, **payload: Any) -> Any:
        return self._wallet.step_up(action="lockdown_release", **payload)
