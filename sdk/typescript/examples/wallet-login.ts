import { BitcoinBastionClient, type WalletProofSigner } from "../src/index.js";
declare const externalWallet: WalletProofSigner; // User-wallet adapter; never submit a private key.
const client = new BitcoinBastionClient({ baseUrl: "https://api.example.test" });
const challenge = await client.walletAuth.createChallenge({ action: "login", network: "bitcoin-mainnet", proofType: "bip322", origin: "https://app.example.test", deviceKeyFingerprint: "sha256:" + "0".repeat(64) });
console.info(challenge.canonicalIntent, challenge.safetyWarning);
const proof = await externalWallet.signWalletIntent({ intent: challenge.canonicalIntent, network: challenge.network, action: "login" });
await client.walletAuth.login({ challengeId: challenge.challengeId, proof });
