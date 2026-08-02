from fastapi.testclient import TestClient

from app.main import app


def test_wallet_signature_or_bearer_alone_cannot_access_me():
    client = TestClient(app)
    assert client.get("/api/v1/wallet-auth/me", headers={"Bastion-Wallet-Signature": "raw"}).status_code == 401
    response = client.get("/api/v1/wallet-auth/me", headers={"Authorization": "Bearer access-pass"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "wallet_session_invalid"


def test_pop_requires_all_request_signature_headers():
    response = TestClient(app).get("/api/v1/wallet-auth/me", headers={"Authorization": "PoP sess_fictional"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "wallet_session_invalid"


def test_public_schemas_have_no_seed_or_private_key_fields():
    schema = TestClient(app).get("/openapi.json").json()
    names = (
        "WalletApiChallengeRequest", "WalletRegisterRequest", "WalletLoginRequest",
        "WalletApiSessionRequest", "WalletApiStepUpRequest", "WalletApiRecoveryStartRequest",
        "WalletApiRecoveryFactorRequest", "WalletApiRecoveryCompleteRequest",
    )
    request_schemas = str({name: schema["components"]["schemas"][name] for name in names}).lower()
    for forbidden in ('"seed"', '"mnemonic"', '"xprv"', '"private_key"', '"password"', '"email"'):
        assert forbidden not in request_schemas
