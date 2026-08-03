from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

from bastion_ui.access_client import AccessApiClient


@dataclass(frozen=True)
class WalletAuthApiClient(AccessApiClient):
    """Thin frontend adapter for the implemented `/api/v1/wallet-auth` router."""

    def create_challenge(
        self,
        certificate_fingerprint: dict[str, Any] | str,
        requested_scopes: list[str] | None = None,
        origin: str | None = None,
    ) -> dict[str, Any]:
        if not isinstance(certificate_fingerprint, dict):
            raise TypeError("Wallet Auth challenge requires its backend request object")
        return self._post("/api/v1/wallet-auth/challenges", certificate_fingerprint)

    def register(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._post("/api/v1/wallet-auth/register", payload)

    def login(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._post("/api/v1/wallet-auth/login", payload)

    def create_session(
        self,
        challenge_id: dict[str, Any] | str,
        signature: str | None = None,
        device_fingerprint: str | None = None,
    ) -> dict[str, Any]:
        if not isinstance(challenge_id, dict):
            raise TypeError("Wallet Auth session requires its backend request object")
        return self._post("/api/v1/wallet-auth/sessions", challenge_id)

    def principal(self, headers: dict[str, str]) -> dict[str, Any]:
        return self._get("/api/v1/wallet-auth/me", headers=headers)

    def entitlements(self, headers: dict[str, str]) -> dict[str, Any]:
        return self._get("/api/v1/wallet-auth/entitlements", headers=headers)

    def devices(self, headers: dict[str, str]) -> dict[str, Any]:
        return self._get("/api/v1/wallet-auth/devices", headers=headers)

    def revoke_device(self, device_id: str, headers: dict[str, str]) -> dict[str, Any]:
        return self._delete(f"/api/v1/wallet-auth/devices/{quote(device_id, safe='')}", headers)

    def step_up(self, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
        return self._post("/api/v1/wallet-auth/step-up", payload, headers=headers)

    def recovery_start(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._post("/api/v1/wallet-auth/recovery/start", payload)

    def recovery_status(self, recovery_id: str) -> dict[str, Any]:
        return self._get(f"/api/v1/wallet-auth/recovery/{quote(recovery_id, safe='')}")

    def recovery_complete(self, recovery_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._post(
            f"/api/v1/wallet-auth/recovery/{quote(recovery_id, safe='')}/complete", payload
        )

    def lockdown(self, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
        return self._post("/api/v1/wallet-auth/lockdown", payload, headers=headers)
