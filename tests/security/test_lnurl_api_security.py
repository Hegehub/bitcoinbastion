from fastapi.testclient import TestClient

from app.main import app


def test_lnurl_credential_is_not_bearer_access_and_withdraw_is_policy_protected():
    client = TestClient(app)
    headers = {"Authorization": "Bearer lnurl-linking-key"}
    assert client.post("/v1/lnurl/withdraw/requests", headers=headers, json={"amount_msat": 1000, "purpose": "reward", "description": "reward"}).status_code == 401
    assert client.get("/api/v1/wallet-auth/me", headers=headers).status_code == 401


def test_protocol_cors_is_narrow_and_no_host_domain_substitution():
    client = TestClient(app)
    callback = client.get("/v1/lnurl/auth/callback?k1=" + "01" * 32 + "&key=02" + "02" * 32 + "&sig=3001", headers={"Host": "attacker.example"})
    assert callback.headers["access-control-allow-origin"] == "*"
    assert "attacker.example" not in callback.text
    protected = client.post("/v1/lnurl/auth/challenges", json={"action": "login", "origin": "https://bitcoin-bastion.com"})
    assert "access-control-allow-origin" not in protected.headers


def test_lnurl_openapi_has_no_secret_inputs_or_bearer_scheme():
    schema = TestClient(app).get("/openapi.json").json()
    paths = {path: value for path, value in schema["paths"].items() if path.startswith("/v1/lnurl")}
    serialized = str(paths).lower()
    for forbidden in ('"seed"', '"mnemonic"', '"xprv"', '"private_key"', 'bearer <lnurl'):
        assert forbidden not in serialized
    for operations in paths.values():
        for operation in operations.values():
            assert operation["x-lnurl-auth-grants-access-alone"] is False
            assert operation["x-invoice-creation-means-settled"] is False
