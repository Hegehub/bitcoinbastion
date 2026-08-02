import pytest

from bitcoin_bastion_sdk.errors import BitcoinWalletSecretForbiddenError
from bitcoin_bastion_sdk.safety import assert_safe
from bitcoin_bastion_sdk.wallet_auth.proofs import WalletProof


@pytest.mark.parametrize("key", ["seed", "mnemonic", "wallet_seed", "bitcoin_seed", "private_key", "xprv", "wif"])
def test_wallet_secrets_are_rejected_without_echo(key: str) -> None:
    secret = "never echo this wallet secret"
    with pytest.raises(BitcoinWalletSecretForbiddenError) as captured:
        assert_safe({key: secret})
    assert secret not in str(captured.value)


def test_legacy_proof_is_explicitly_compatibility_and_repr_is_safe() -> None:
    proof = WalletProof("legacy_message_signature", "raw-wallet-signature", "bc1qidentifier")
    assert proof.expected_strength == "compatibility"
    assert "raw-wallet-signature" not in repr(proof)
    assert "bc1qidentifier" not in repr(proof)
