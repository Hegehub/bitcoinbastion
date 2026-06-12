from __future__ import annotations

from typer.testing import CliRunner

from cli.bastion_cli.main import app

runner = CliRunner()

FORBIDDEN_WORDING = (
    "clean address",
    "dirty address",
    "criminal address",
    "guaranteed safe",
    "approved payment",
    "verified illicit",
)


class _Trace:
    def __init__(self) -> None:
        self.addresses: list[str] = []

    def analyze_address(self, address: str) -> dict[str, object]:
        self.addresses.append(address)
        return {"address": address, "no_custody": True}


class _Client:
    def __init__(self) -> None:
        self.trace = _Trace()

    def __enter__(self) -> "_Client":
        return self

    def __exit__(self, *args: object) -> None:
        return None


def test_trace_address_rejects_seed_phrase() -> None:
    result = runner.invoke(app, ["trace", "address", "seed phrase should fail"])
    assert result.exit_code != 0
    assert "Never submit seed phrases" in result.output


def test_trace_address_rejects_private_key() -> None:
    result = runner.invoke(app, ["trace", "address", "private key should fail"])
    assert result.exit_code != 0


def test_trace_address_rejects_xprv() -> None:
    result = runner.invoke(app, ["trace", "address", "xprv123"])
    assert result.exit_code != 0


def test_trace_address_rejects_wallet_dat() -> None:
    result = runner.invoke(app, ["trace", "address", "wallet.dat"])
    assert result.exit_code != 0


def test_trace_address_accepts_plausible_public_bitcoin_address(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    client = _Client()
    monkeypatch.setattr("cli.bastion_cli.commands._common.make_client", lambda config: client)
    address = "bc1qexamplepublicaddress000000000000000000000"

    result = runner.invoke(app, ["--output", "json", "trace", "address", address])

    assert result.exit_code == 0, result.output
    assert client.trace.addresses == [address]
    assert "Advisory-only" in result.output


def test_trace_safety_copy_appears_in_help_and_forbidden_wording_absent() -> None:
    result = runner.invoke(app, ["trace", "--help"])
    assert result.exit_code == 0
    assert "Advisory-only" in result.output
    checked = result.output.casefold()
    for phrase in FORBIDDEN_WORDING:
        assert phrase not in checked
