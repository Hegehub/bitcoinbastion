"""Safe external-wallet flow: this example never imports wallet secrets."""

from bitcoin_bastion_sdk import BastionClient

client = BastionClient(base_url="https://bastion.example")
challenge = client.auth.wallet.create_challenge(
    action="login",
    network="bitcoin-mainnet",
    proof_type="bip322",
    origin="https://bastion.example",
)
print(challenge.safety_warning)
print(challenge.signable_intent)
print("Sign the structured intent in an external BIP-322-capable wallet, then submit it.")
