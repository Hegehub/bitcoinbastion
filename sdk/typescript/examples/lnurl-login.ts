import { BitcoinBastionClient, type LnurlWalletAdapter } from "../src/index.js";
declare const wallet: LnurlWalletAdapter;
const client = new BitcoinBastionClient({ baseUrl: "https://api.example.test", expectedLnurlAuthDomain: "auth.example.test" });
const challenge = await client.lnurlAuth.createChallenge({ action: "login", origin: "https://app.example.test", device_key_fingerprint: "sha256:" + "0".repeat(64) });
console.info(challenge.lnurl, challenge.domain); // Render QR separately; user approves in wallet.
await client.lnurlAuth.open(challenge, wallet);
