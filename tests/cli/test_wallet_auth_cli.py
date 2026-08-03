from typer.testing import CliRunner
from cli.bastion_cli.main import app

runner = CliRunner()


class Wallet:
    def create_challenge(self, **kw):
        return {
            "challenge_id": "c",
            "canonical_intent": "Sign this",
            "expires_at": "soon",
            "network": kw["network"],
        }

    def get_principal(self):
        return {"principal_type": "bitcoin_wallet_principal", "session_token": "secret"}

    def get_entitlements(self):
        return {"plan": "basic"}

    def list_devices(self):
        return [{"device_id": "wdev_12345678"}]

    def revoke_device(self, value):
        return {"revoked": value}

    def start_recovery(self, **kw):
        return {"recovery_id": "wrec_12345678"}

    def start_lockdown(self, **kw):
        return {"status": "locked"}


class Auth:
    wallet = Wallet()


class Client:
    auth = Auth()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


def test_challenge_and_safe_output(monkeypatch):
    monkeypatch.setattr("cli.bastion_cli.commands._common.make_client", lambda config: Client())
    result = runner.invoke(
        app,
        [
            "--output",
            "json",
            "wallet-auth",
            "challenge",
            "--action",
            "login",
            "--device-key-fingerprint",
            "sha256:x",
            "--origin",
            "https://app.test",
        ],
    )
    assert result.exit_code == 0
    assert "does not authorize a Bitcoin transaction" in result.output
    assert "seed" in result.output


def test_management_commands(monkeypatch):
    monkeypatch.setattr("cli.bastion_cli.commands._common.make_client", lambda config: Client())
    for args in (
        ["me"],
        ["entitlements"],
        ["devices"],
        ["device-revoke", "wdev_12345678"],
        [
            "recovery-start",
            "--principal-reference",
            "ref",
            "--recovery-profile",
            "standard",
            "--new-device-public-key",
            "public",
        ],
        ["lockdown", "--reason", "compromise", "--yes"],
    ):
        assert runner.invoke(app, ["--output", "json", "wallet-auth", *args]).exit_code == 0


def test_no_wallet_secret_options():
    result = runner.invoke(app, ["wallet-auth", "register", "--help"])
    for forbidden in (
        "--seed",
        "--mnemonic",
        "--xprv",
        "--private-key",
        "--wallet-seed",
        "--bitcoin-seed",
    ):
        assert forbidden not in result.output
