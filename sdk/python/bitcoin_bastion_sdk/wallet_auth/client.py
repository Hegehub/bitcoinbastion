from __future__ import annotations

from datetime import datetime
from typing import Any

from bitcoin_bastion_sdk.safety import assert_safe
from bitcoin_bastion_sdk.wallet_auth.intents import BastionAuthIntent


class WalletAuthClient:
    def __init__(self, transport: Any) -> None:
        self._transport = transport

    def create_challenge(self, **payload: Any) -> BastionAuthIntent:
        assert_safe(payload)
        result = self._transport.request("POST", "/wallet-auth/challenges", json=payload)
        return BastionAuthIntent(
            version=int(result.get("intent_version", 1)),
            domain=str(payload.get("origin", "")),
            action=str(payload["action"]),
            network=str(result["network"]),
            challenge_id=str(result["challenge_id"]),
            canonical_intent=str(result["canonical_intent"]),
            intent_hash=str(result["intent_hash"]),
            expires_at=datetime.fromisoformat(str(result["expires_at"]).replace("Z", "+00:00")),
            device_key_fingerprint=payload.get("device_key_fingerprint"),
        )

    def register(self, **payload: Any) -> Any:
        assert_safe(payload)
        return self._transport.request("POST", "/wallet-auth/register", json=payload)

    def login(self, **payload: Any) -> Any:
        assert_safe(payload)
        return self._transport.request("POST", "/wallet-auth/login", json=payload)

    def create_session(self, **payload: Any) -> Any:
        assert_safe(payload)
        return self._transport.request("POST", "/wallet-auth/sessions", json=payload)

    def step_up(self, **payload: Any) -> Any:
        return self._transport.request("POST", "/wallet-auth/step-up", json=payload, require_auth=True)

    def get_principal(self) -> Any:
        return self._transport.request("GET", "/wallet-auth/me", require_auth=True)

    def get_entitlements(self) -> Any:
        return self._transport.request("GET", "/wallet-auth/entitlements", require_auth=True)

    def list_devices(self) -> Any:
        return self._transport.request("GET", "/wallet-auth/devices", require_auth=True)

    def revoke_device(self, device_id: str) -> Any:
        return self._transport.request("DELETE", f"/wallet-auth/devices/{device_id}", require_auth=True)

    def start_lockdown(self, **payload: Any) -> Any:
        return self._transport.request("POST", "/wallet-auth/lockdown", json=payload, require_auth=True)

    def start_recovery(self, **payload: Any) -> Any:
        assert_safe(payload)
        return self._transport.request("POST", "/wallet-auth/recovery/start", json=payload)

    def recovery_status(self, recovery_id: str) -> Any:
        return self._transport.request("GET", f"/wallet-auth/recovery/{recovery_id}")

    def submit_recovery_factor(self, recovery_id: str, **payload: Any) -> Any:
        assert_safe(payload)
        return self._transport.request("POST", f"/wallet-auth/recovery/{recovery_id}/factor", json=payload)

    def complete_recovery(self, recovery_id: str, **payload: Any) -> Any:
        assert_safe(payload)
        return self._transport.request("POST", f"/wallet-auth/recovery/{recovery_id}/complete", json=payload)


class AsyncWalletAuthClient:
    def __init__(self, transport: Any) -> None:
        self._transport = transport

    async def create_challenge(self, **payload: Any) -> BastionAuthIntent:
        assert_safe(payload)
        result = await self._transport.request("POST", "/wallet-auth/challenges", json=payload)
        return BastionAuthIntent(
            version=int(result.get("intent_version", 1)),
            domain=str(payload.get("origin", "")),
            action=str(payload["action"]),
            network=str(result["network"]),
            challenge_id=str(result["challenge_id"]),
            canonical_intent=str(result["canonical_intent"]),
            intent_hash=str(result["intent_hash"]),
            expires_at=datetime.fromisoformat(str(result["expires_at"]).replace("Z", "+00:00")),
        )

    async def login(self, **payload: Any) -> Any:
        assert_safe(payload)
        return await self._transport.request("POST", "/wallet-auth/login", json=payload)

    async def create_session(self, **payload: Any) -> Any:
        return await self._transport.request("POST", "/wallet-auth/sessions", json=payload)

    async def get_principal(self) -> Any:
        return await self._transport.request("GET", "/wallet-auth/me", require_auth=True)

    async def get_entitlements(self) -> Any:
        return await self._transport.request("GET", "/wallet-auth/entitlements", require_auth=True)
