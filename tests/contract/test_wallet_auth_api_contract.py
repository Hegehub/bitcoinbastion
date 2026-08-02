from fastapi.testclient import TestClient

from app.main import app


REQUIRED = {
    "/api/v1/wallet-auth/challenges", "/api/v1/wallet-auth/register",
    "/api/v1/wallet-auth/login", "/api/v1/wallet-auth/sessions",
    "/api/v1/wallet-auth/step-up", "/api/v1/wallet-auth/me",
    "/api/v1/wallet-auth/entitlements", "/api/v1/wallet-auth/devices",
    "/api/v1/wallet-auth/devices/{device_id}", "/api/v1/wallet-auth/wallets",
    "/api/v1/wallet-auth/wallets/{proof_id}", "/api/v1/wallet-auth/lockdown",
    "/api/v1/wallet-auth/lockdown/status", "/api/v1/wallet-auth/recovery/start",
    "/api/v1/wallet-auth/recovery/{recovery_id}",
    "/api/v1/wallet-auth/recovery/{recovery_id}/factor",
    "/api/v1/wallet-auth/recovery/{recovery_id}/complete",
}


def test_wallet_auth_openapi_contract_and_safety_metadata():
    schema = TestClient(app).get("/openapi.json").json()
    assert REQUIRED <= set(schema["paths"])
    assert "BastionWalletPoPSession" in schema["components"]["securitySchemes"]
    for path in REQUIRED:
        for operation in schema["paths"][path].values():
            assert operation["x-wallet-signature-grants-access-alone"] is False
            assert operation["x-bitcoin-seed-or-private-key-requested"] is False
    wallet_operations = str({path: schema["paths"][path] for path in REQUIRED}).lower()
    assert "password auth" not in wallet_operations
    assert "/api/v1/lnurl" not in " ".join(REQUIRED)
