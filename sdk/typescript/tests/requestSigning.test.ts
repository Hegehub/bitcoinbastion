import { createHmac } from "node:crypto";
import { describe, expect, it } from "vitest";
import { BastionAccessAuth, bodyHash, buildRequestDigest, canonicalJson, type AccessSigner } from "../src/index.js";

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

describe("request signing", () => {
  it("body hash changes when body changes", () => {
    expect(bodyHash({ a: 1 })).not.toEqual(bodyHash({ a: 2 }));
  });

  it("canonical JSON order is stable", () => {
    expect(canonicalJson({ b: 2, a: 1 })).toBe(canonicalJson({ a: 1, b: 2 }));
    expect(bodyHash({ b: 2, a: 1 })).toBe(bodyHash({ a: 1, b: 2 }));
  });

  it("nonce is unique between requests", async () => {
    const nonces = new Set<string>();
    for (let i = 0; i < 10; i += 1) nonces.add((await auth().signRequest("GET", "/x"))["X-Bastion-Nonce"]);
    expect(nonces.size).toBe(10);
  });

  it("method and path are included in digest", () => {
    const digestA = buildRequestDigest({ method: "GET", path: "/a", bodyHash: bodyHash(undefined), timestamp: "t", nonce: "n" });
    const digestB = buildRequestDigest({ method: "POST", path: "/b", bodyHash: bodyHash(undefined), timestamp: "t", nonce: "n" });
    expect(digestA).not.toEqual(digestB);
  });
});
