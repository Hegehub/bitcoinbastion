import { createHmac } from "node:crypto";
import { describe, expect, it } from "vitest";
import { BastionAccessAuth, type AccessSigner } from "../src/index.js";

const signer: AccessSigner = {
  getPublicKeyFingerprint: () => "sha256:test-device",
  signDigest: (digest) => `sig_${createHmac("sha256", "secret").update(digest).digest("hex")}`,
};

function auth(): BastionAccessAuth {
  return new BastionAccessAuth({
    sessionToken: "sess_secret_token",
    sessionExpiresAt: new Date(Date.now() + 60_000).toISOString(),
    deviceKeyProvider: signer,
  });
}

describe("BastionAccessAuth", () => {
  it("produces all required Proof-of-Access headers", async () => {
    const headers = await auth().signRequest("POST", "/api/v1/access/me", { ok: true });
    expect(headers["X-Bastion-Session"]).toBe("sess_secret_token");
    expect(headers["X-Bastion-Timestamp"]).toBeTruthy();
    expect(headers["X-Bastion-Nonce"]).toHaveLength(32);
    expect(headers["X-Bastion-Body-Hash"]).toMatch(/^sha256:/);
    expect(headers["X-Bastion-Signature"]).toMatch(/^sig_/);
    expect(headers["X-Bastion-Auth-Version"]).toBe("proof-of-access-v1");
  });

  it("exports safe redacted state", () => {
    const provider = new BastionAccessAuth({ accessPass: "bbp_live_abcdef123456", sessionToken: "sess_secret123456", deviceKeyProvider: signer });
    expect(JSON.stringify(provider.exportSafeAccessState())).not.toContain("bbp_live_abcdef123456");
    expect(JSON.stringify(provider.exportSafeAccessState())).not.toContain("sess_secret123456");
  });
});
