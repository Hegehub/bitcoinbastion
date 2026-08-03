from typer.testing import CliRunner
from cli.bastion_cli.main import app

runner = CliRunner()


class LN:
    def create_auth_challenge(self, **kw):
        return {
            "challenge_id": "a",
            "lnurl": "LNURL1PUBLIC",
            "auth_domain": "auth.test",
            "action": kw["action"],
            "k1": "must-not-print",
        }

    def create_subscription_payment(self, **kw):
        return {
            "payment_id": "p",
            "state": "created",
            "lnurl": "LNURL1PAY",
            "comment_allowed": 4,
            "entitlement_active": False,
        }

    def verify_payment(self, p):
        return {"payment_id": p, "state": "pending", "entitlement_active": True}

    def request_withdraw(self, **kw):
        return {"policy_approved": True, "lnurl": "LNURL1WITHDRAW"}


class Auth:
    lnurl = LN()


class Client:
    auth = Auth()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        pass


def test_auth_hides_k1(monkeypatch):
    monkeypatch.setattr("cli.bastion_cli.commands._common.make_client", lambda c: Client())
    r = runner.invoke(
        app,
        [
            "--output",
            "json",
            "lnurl",
            "auth-login",
            "--origin",
            "https://app.test",
            "--device-key-fingerprint",
            "sha256:x",
        ],
    )
    assert (
        r.exit_code == 0
        and "LNURL1PUBLIC" in r.output
        and "must-not-print" not in r.output
        and "Device-bound PoP" in r.output
    )


def test_pay_never_activates_before_settlement(monkeypatch):
    monkeypatch.setattr("cli.bastion_cli.commands._common.make_client", lambda c: Client())
    created = runner.invoke(app, ["--output", "json", "lnurl", "pay", "--plan", "pro_pass"])
    assert '"entitlement_active": false' in created.output
    pending = runner.invoke(app, ["--output", "json", "lnurl", "pay-status", "p"])
    assert '"entitlement_active": false' in pending.output


def test_comment_limit_and_policy_approved_withdraw(monkeypatch):
    monkeypatch.setattr("cli.bastion_cli.commands._common.make_client", lambda c: Client())
    assert (
        runner.invoke(app, ["lnurl", "pay", "--plan", "pro", "--comment", "12345"]).exit_code == 2
    )
    assert (
        runner.invoke(
            app,
            [
                "lnurl",
                "withdraw",
                "--amount-msat",
                "1000",
                "--purpose",
                "refund",
                "--reason",
                "return",
            ],
        ).exit_code
        == 0
    )
