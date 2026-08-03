import pytest
from cli.bastion_cli.security.local_vault import reject_wallet_secrets


@pytest.mark.parametrize(
    "field",
    [
        "seed",
        "seedPhrase",
        "mnemonic",
        "privateKey",
        "walletPrivateKey",
        "xprv",
        "bitcoinSeed",
        "lightningSeed",
    ],
)
def test_wallet_secret_fields_rejected(field):
    with pytest.raises(ValueError, match="does not require"):
        reject_wallet_secrets({field: "secret"})
