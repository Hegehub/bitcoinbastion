import { createHmac } from "node:crypto";
import { BastionAccessAuth, BitcoinBastionClient, type AccessSigner } from "../src/index.js";

const baseUrl = process.env.BASTION_API_BASE_URL ?? "http://localhost:8000";
const sessionToken = process.env.BASTION_SESSION_TOKEN;

if (!sessionToken) throw new Error("Set BASTION_SESSION_TOKEN from the Proof-of-Access session flow.");

const signer: AccessSigner = {
  getPublicKeyFingerprint: () => "sha256:example-device",
  signDigest: (digest) => `sig_${createHmac("sha256", "example-bastion-device-secret").update(digest).digest("hex")}`,
};

const auth = new BastionAccessAuth({
  sessionToken,
  sessionExpiresAt: new Date(Date.now() + 15 * 60_000).toISOString(),
  deviceKeyProvider: signer,
});

const client = new BitcoinBastionClient({
  baseUrl,
  accessAuth: {
    sessionToken,
    sessionExpiresAt: new Date(Date.now() + 15 * 60_000).toISOString(),
    deviceKeyProvider: signer,
  },
});

console.log("Safe auth state", auth.exportSafeAccessState());
console.log(await client.access.me());
