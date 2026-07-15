import importlib


def test_wallet_auth_domain_import_is_side_effect_safe(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("REDIS_URL", raising=False)
    module = importlib.import_module("app.domain.wallet_auth")
    assert module.WalletNetwork.BITCOIN_MAINNET.value == "bitcoin-mainnet"


def test_lnurl_domain_import_is_side_effect_safe(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("REDIS_URL", raising=False)
    module = importlib.import_module("app.domain.lnurl")
    assert module.LNURL_K1_BYTES == 32


def test_imports_do_not_pull_runtime_frameworks() -> None:
    wallet_module = importlib.import_module("app.domain.wallet_auth")
    lnurl_module = importlib.import_module("app.domain.lnurl")
    assert not hasattr(wallet_module, "FastAPI")
    assert not hasattr(wallet_module, "Session")
    assert not hasattr(lnurl_module, "FastAPI")
    assert not hasattr(lnurl_module, "Session")
