import { BitcoinBastionClient, WalletLnurlAuthProvider, type BastionPopSigner } from "../src/index.js";
declare const secureDeviceSigner: BastionPopSigner;
const auth = new WalletLnurlAuthProvider(secureDeviceSigner, { sessionToken: "session-from-backend", principalHash: "sha256:public-principal", principalType: "bitcoin_wallet_principal", expiresAt: "2099-08-02T12:15:00Z", scopes: ["wallet:read"] });
const client = new BitcoinBastionClient({ baseUrl: "https://api.example.test", auth });
await client.walletAuth.getPrincipal(); // Central transport adds a fresh PoP signature and nonce.
