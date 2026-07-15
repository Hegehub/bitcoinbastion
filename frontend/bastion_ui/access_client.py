from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

import httpx

from bastion_ui.config import get_config


@dataclass(frozen=True)
class AccessApiClient:
    base_url: str | None = None
    timeout_seconds: float | None = None

    @property
    def _base_url(self) -> str:
        return (self.base_url or get_config().api_base_url).rstrip("/")

    @property
    def _timeout(self) -> float:
        return self.timeout_seconds or get_config().request_timeout_seconds

    def _url(self, path: str) -> str:
        return f"{self._base_url}{path}"

    def _post(
        self, path: str, payload: dict[str, Any], headers: dict[str, str] | None = None
    ) -> dict[str, Any]:
        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(self._url(path), json=payload, headers=headers)
            response.raise_for_status()
            return cast(dict[str, Any], response.json())

    def _get(self, path: str, headers: dict[str, str] | None = None) -> dict[str, Any]:
        with httpx.Client(timeout=self._timeout) as client:
            response = client.get(self._url(path), headers=headers)
            response.raise_for_status()
            return cast(dict[str, Any], response.json())

    def create_payment_intent(self, plan_code: str) -> dict[str, Any]:
        return self._post("/v1/access/payment-intents", {"plan_code": plan_code})

    def get_payment_intent(self, payment_intent_id: str) -> dict[str, Any]:
        return self._get(f"/v1/access/payment-intents/{payment_intent_id}")

    def issue_certificate(
        self, payment_intent_id: str, device_public_key: str | None = None
    ) -> dict[str, Any]:
        return self._post(
            "/v1/access/certificates",
            {"payment_intent_id": payment_intent_id, "device_public_key": device_public_key},
        )

    def create_challenge(
        self, certificate_fingerprint: str, requested_scopes: list[str], origin: str
    ) -> dict[str, Any]:
        return self._post(
            "/v1/access/challenges",
            {
                "certificate_fingerprint": certificate_fingerprint,
                "requested_scopes": requested_scopes,
                "origin": origin,
            },
        )

    def create_session(
        self, challenge_id: str, signature: str, device_fingerprint: str
    ) -> dict[str, Any]:
        return self._post(
            "/v1/access/sessions",
            {
                "challenge_id": challenge_id,
                "challenge_signature": signature,
                "device_fingerprint": device_fingerprint,
            },
        )

    def get_access_me(self, headers: dict[str, str]) -> dict[str, Any]:
        return self._get("/v1/access/me", headers=headers)

    def get_access_entitlements(self, headers: dict[str, str]) -> dict[str, Any]:
        return self._get("/v1/access/entitlements", headers=headers)

    def get_access_limits(self, headers: dict[str, str]) -> dict[str, Any]:
        return self._get("/v1/access/limits", headers=headers)

    def start_recovery(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._post("/v1/access/recovery/start", payload)

    def get_recovery_status(self, recovery_attempt_id: str) -> dict[str, Any]:
        return self._get(f"/v1/access/recovery/status/{recovery_attempt_id}")

    def lockdown(self, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
        return self._post("/v1/access/lockdown", payload, headers=headers)
