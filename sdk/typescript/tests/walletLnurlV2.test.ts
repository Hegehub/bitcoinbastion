import { describe, expect, it, vi } from "vitest";
import { BitcoinBastionClient, WalletLnurlAuthProvider, canonicalizeQuery, canonicalizeRequest, hashRequestBody, assertNoWalletSecretFields, redactSensitive } from "../src/index.js";

const response = (data: unknown) => new Response(JSON.stringify({ data }), { status: 200, headers: { "content-type": "application/json" } });

describe("Wallet-first PoP v2", () => {
  it("matches the Python/backend contract vector", () => {
    const body = '{"plan":"pro_pass","scopes":["market:intelligence:read"]}';
    const query = { z: "two words", a: "1" };
    expect(canonicalizeQuery(query)).toBe("a=1&z=two%20words");
    expect(hashRequestBody(body)).toBe("76800918ee939dd77abd01fc70466882d7d83eff9b6178a5268623ea21ed930e");
    expect(canonicalizeRequest({ method: "POST", path: "/api/v1/wallet-auth/me", query, serializedBody: body, timestamp: "2026-08-02T12:00:00Z", nonce: "00112233445566778899aabbccddeeff" })).toContain("/api/v1/wallet-auth/me?a=1&z=two%20words");
  });
  it("uses PoP headers and fresh nonce/signature on every request", async () => {
    let n = 0; const signed: Uint8Array[] = [];
    const auth = new WalletLnurlAuthProvider({ publicKeyFingerprint: "sha256:device", sign: async data => { signed.push(data); return `sig-${signed.length}`; } }, { sessionToken: "sess_secret", principalHash: "sha256:principal", principalType: "bitcoin_wallet_principal", expiresAt: "2099-01-01T00:00:00Z", scopes: [] }, () => new Date("2026-08-02T12:00:00Z"), () => `nonce-${++n}`);
    const fetchImpl = vi.fn(async () => response({ ok: true }));
    const client = new BitcoinBastionClient({ baseUrl: "https://example.test", auth, fetchImpl });
    await client.walletAuth.getPrincipal(); await client.walletAuth.getPrincipal();
    const headers = fetchImpl.mock.calls.map(call => call[1]?.headers as Record<string, string>);
    expect(headers[0]?.Authorization).toBe("PoP sess_secret");
    expect(headers[0]?.["Bastion-Request-Nonce"]).not.toBe(headers[1]?.["Bastion-Request-Nonce"]);
    expect(headers[0]?.["Bastion-Request-Signature"]).not.toBe(headers[1]?.["Bastion-Request-Signature"]);
  });
  it("does not inject Bearer by default", async () => {
    const fetchImpl = vi.fn(async () => response({ ok: true }));
    const client = new BitcoinBastionClient({ baseUrl: "https://example.test", fetchImpl });
    await client.signals.latest();
    expect((fetchImpl.mock.calls[0]?.[1]?.headers as Record<string, string>).Authorization).toBeUndefined();
  });
});

describe("auth safety", () => {
  for (const key of ["mnemonic", "seed", "seedPhrase", "xprv", "walletPrivateKey", "lightningSeed"]) it(`rejects ${key}`, () => expect(() => assertNoWalletSecretFields({ [key]: "secret" })).toThrow("does not require"));
  it("redacts PoP, LNURL, and recovery secrets without mutation", () => { const source = { sessionToken: "sess_secret", k1: "raw", signature: "sig", recoveryMaterial: "factor" }; const result = redactSensitive(source) as Record<string, unknown>; expect(Object.values(result)).not.toContain("raw"); expect(source.k1).toBe("raw"); });
  it("invoice issuance is not settlement", async () => { const client = new BitcoinBastionClient({ baseUrl: "https://example.test", fetchImpl: async () => new Response(JSON.stringify({ status: "invoice_issued", payment_id: "pay_1", settled: false, entitlement_active: true }), { status: 200 }) }); const state = await client.lnurlPay.verifyPayment("pay_1"); expect(state.settled).toBe(false); expect(state.entitlementActive).toBe(false); });
});
