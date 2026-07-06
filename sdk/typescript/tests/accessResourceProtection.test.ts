import { createHmac } from "node:crypto";
import { describe, expect, it } from "vitest";
import { AccessAuthRequiredError, BitcoinBastionClient, type AccessSigner } from "../src/index.js";

function jsonResponse(body: unknown): Response {
  return new Response(JSON.stringify(body), { status: 200, headers: { "content-type": "application/json" } });
}

const signer: AccessSigner = {
  getPublicKeyFingerprint: () => "sha256:test-device",
  signDigest: (digest) => `sig_${createHmac("sha256", "secret").update(digest).digest("hex")}`,
};

describe("protected resources", () => {
  it("protected resource without session throws AccessAuthRequiredError", async () => {
    const client = new BitcoinBastionClient({ baseUrl: "http://localhost:8000", fetchImpl: async () => jsonResponse({}) });
    await expect(client.access.me()).rejects.toBeInstanceOf(AccessAuthRequiredError);
    await expect(client.treasury.listRequests()).rejects.toBeInstanceOf(AccessAuthRequiredError);
  });

  it("public resource does not require auth", async () => {
    const calls: RequestInit[] = [];
    const client = new BitcoinBastionClient({
      baseUrl: "http://localhost:8000",
      fetchImpl: async (_input, init) => {
        calls.push(init ?? {});
        return jsonResponse({ data: { ok: true }, error: null });
      },
    });
    await expect(client.providerHealth.status()).resolves.toEqual({ ok: true });
    expect(calls[0]?.headers).not.toHaveProperty("X-Bastion-Session");
  });

  it("protected resource with signed session adds Proof-of-Access headers", async () => {
    const calls: RequestInit[] = [];
    const client = new BitcoinBastionClient({
      baseUrl: "http://localhost:8000",
      accessAuth: {
        sessionToken: "sess_secret_token",
        sessionExpiresAt: new Date(Date.now() + 60_000).toISOString(),
        deviceKeyProvider: signer,
      },
      fetchImpl: async (_input, init) => {
        calls.push(init ?? {});
        return jsonResponse({ data: { ok: true }, error: null });
      },
    });
    await expect(client.access.me()).resolves.toEqual({ ok: true });
    expect(calls[0]?.headers).toMatchObject({
      "X-Bastion-Session": "sess_secret_token",
      "X-Bastion-Auth-Version": "proof-of-access-v1",
    });
  });
});
