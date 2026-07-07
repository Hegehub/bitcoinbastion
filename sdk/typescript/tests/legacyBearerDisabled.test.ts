import { describe, expect, it, vi } from "vitest";
import { BitcoinBastionClient, LegacyAuthDisabledError } from "../src/index.js";

function jsonResponse(body: unknown): Response {
  return new Response(JSON.stringify(body), { status: 200, headers: { "content-type": "application/json" } });
}

describe("legacy bearer auth", () => {
  it("does not use Authorization: Bearer by default", async () => {
    const calls: RequestInit[] = [];
    const fetchImpl: typeof fetch = async (_input, init) => {
      calls.push(init ?? {});
      return jsonResponse({ data: { ok: true }, error: null });
    };
    const client = new BitcoinBastionClient({ baseUrl: "http://localhost:8000", fetchImpl });
    await client.providerHealth.status();
    expect(calls[0]?.headers).not.toMatchObject({ Authorization: expect.any(String) });
  });

  it("legacy bearer path is disabled", async () => {
    const client = new BitcoinBastionClient({ baseUrl: "http://localhost:8000", apiKey: "legacy", fetchImpl: async () => jsonResponse({ data: { ok: true }, error: null }) });
    await expect(client.providerHealth.status()).rejects.toBeInstanceOf(LegacyAuthDisabledError);
  });

  it("legacy bearer opt-in no longer sends Authorization", async () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => undefined);
    const calls: RequestInit[] = [];
    const fetchImpl: typeof fetch = async (_input, init) => {
      calls.push(init ?? {});
      return jsonResponse({ data: { ok: true }, error: null });
    };
    const client = new BitcoinBastionClient({ baseUrl: "http://localhost:8000", apiKey: "legacy", allowLegacyBearerAuth: true, fetchImpl });
    await expect(client.providerHealth.status()).rejects.toBeInstanceOf(LegacyAuthDisabledError);
    expect(warn).not.toHaveBeenCalled();
    expect(calls).toHaveLength(0);
    warn.mockRestore();
  });
});
