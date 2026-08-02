from __future__ import annotations

import json
from pathlib import Path

import httpx

from bitcoin_bastion_sdk import BastionClient


def test_wallet_auth_routes_and_structured_intent() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"data": {"challenge_id": "wch_safe", "intent_version": 1, "canonical_intent": "{\"action\":\"login\"}", "intent_hash": "sha256:intent", "expires_at": "2026-08-03T00:00:00Z", "network": "bitcoin-mainnet", "proof_type": "bip322"}, "error": None, "meta": {}})

    client = BastionClient(base_url="http://example.com", transport=httpx.MockTransport(handler))
    intent = client.auth.wallet.create_challenge(action="login", network="bitcoin-mainnet", proof_type="bip322", origin="https://bastion.example")
    assert intent.signable_intent.startswith("{")
    assert "does not authorize a Bitcoin transaction" in intent.safety_warning
    assert seen[0].url.path == "/api/v1/wallet-auth/challenges"


def test_cross_sdk_contract_fixture_is_valid() -> None:
    path = Path(__file__).parents[3] / "artifacts" / "wallet_auth_sdk_contract.json"
    payload = json.loads(path.read_text())
    assert payload["authorization_scheme"] == "PoP"
    assert "Bearer" not in json.dumps(payload)
