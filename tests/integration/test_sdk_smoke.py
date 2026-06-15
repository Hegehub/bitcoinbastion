from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_python_sdk_expected_modules_exist() -> None:
    for path in [
        "client.py", "auth.py", "errors.py", "webhooks.py", "websocket.py",
        "schemas/signals.py", "schemas/news.py", "schemas/onchain.py", "schemas/trace.py", "schemas/treasury.py", "schemas/wallet.py",
    ]:
        assert (ROOT / "sdk/python/bitcoin_bastion_sdk" / path).exists(), path


def test_sdk_trace_rejects_sensitive_material() -> None:
    trace = (ROOT / "sdk/python/bitcoin_bastion_sdk/resources/trace.py").read_text(encoding="utf-8")
    safety = (ROOT / "sdk/python/bitcoin_bastion_sdk/safety.py").read_text(encoding="utf-8")
    assert "assert_safe" in trace
    for term in ["seed phrase", "private key", "xprv", "wallet.dat", "signing material"]:
        assert term in safety


def test_typescript_sdk_contract_files_exist() -> None:
    for path in ["package.json", "src/client.ts", "src/resources/trace.ts", "src/resources/webhooks.ts", "src/resources/websocket.ts"]:
        assert (ROOT / "sdk/typescript" / path).exists(), path
