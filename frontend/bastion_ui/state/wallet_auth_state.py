from __future__ import annotations

from typing import Any

import reflex as rx

from bastion_ui.auth_errors import safe_auth_error
from bastion_ui.services.wallet_auth_client import WalletAuthService


class WalletAuthState(rx.State):
    """UI-safe Wallet Proof state. It never stores wallet signatures or session tokens."""

    phase: str = "idle"
    challenge_id: str = ""
    canonical_intent: str = ""
    intent_hash: str = ""
    domain: str = ""
    action: str = "login"
    network: str = "bitcoin-mainnet"
    device_fingerprint: str = ""
    expires_at: str = ""
    proof_method: str = "bip322"
    principal_type: str = ""
    principal_status: str = ""
    device_status: str = ""
    session_status: str = "none"
    error: str = ""

    async def create_challenge(self) -> None:
        self.phase = "challenge_creating"
        self.error = ""
        try:
            result = await WalletAuthService().create_challenge(
                {
                    "action": self.action,
                    "network": self.network,
                    "proof_type": self.proof_method,
                    "origin": self.domain,
                    "device_key_fingerprint": self.device_fingerprint,
                    "requested_scopes": [],
                    "intent_context": {},
                }
            )
            self.challenge_id = str(result.get("challenge_id", ""))
            self.canonical_intent = str(result.get("canonical_intent", ""))
            self.intent_hash = str(result.get("intent_hash", ""))
            self.expires_at = str(result.get("expires_at", ""))
            self.phase = "awaiting_signature"
        except Exception as exc:  # safe boundary; no backend detail reaches UI
            self.phase = "rejected"
            self.error = safe_auth_error(_error_code(exc)).message

    async def submit_external_proof(self, proof: dict[str, Any]) -> None:
        """Submit current-challenge public proof without copying it into Reflex state."""
        self.phase = "proof_submitting"
        try:
            payload = {
                "challenge_id": self.challenge_id,
                "proof_type": self.proof_method,
                "wallet_identifier": proof.get("wallet_identifier"),
                "signature": proof.get("signature"),
                "public_key": proof.get("public_key"),
                "device_key_fingerprint": self.device_fingerprint,
                "origin": self.domain,
                "network": self.network,
            }
            result = await WalletAuthService().login(payload)
            self.principal_type = "Bitcoin Wallet Principal"
            self.principal_status = "verified"
            self.phase = "proof_verified"
            # authentication_grant deliberately remains local. A non-exportable Device signer bridge
            # must consume it immediately to create a session; it is never exposed as public state.
            _ = result.get("authentication_grant")
        except Exception as exc:
            self.phase = "rejected"
            self.error = safe_auth_error(_error_code(exc)).message

    def expire_challenge(self) -> None:
        self.challenge_id = ""
        self.canonical_intent = ""
        self.intent_hash = ""
        self.phase = "expired"


def _error_code(exc: Exception) -> str:
    details = getattr(exc, "details", None)
    if isinstance(details, dict):
        code = details.get("code")
        if isinstance(code, str):
            return code
    return "authentication_error"
