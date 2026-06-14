import { describe, expect, it } from "vitest";
import { BitcoinBastionClient } from "../src/index.js";

function jsonResponse(body: unknown, init: ResponseInit = {}): Response {
  return new Response(JSON.stringify(body), { status: 200, headers: { "content-type": "application/json" }, ...init });
}

describe("BitcoinBastionClient", () => {
  it("creates resources and applies bearer auth", async () => {
    const calls: RequestInit[] = [];
    const fetchImpl: typeof fetch = async (_input, init) => {
      calls.push(init ?? {});
      return jsonResponse({ data: { ok: true }, error: null });
    };
    const client = new BitcoinBastionClient({ baseUrl: "http://localhost:8000/", apiKey: "token", fetchImpl });
    await client.providerHealth.status();
    expect(client.trace).toBeDefined();
    expect(calls[0]?.headers).toMatchObject({ Authorization: "Bearer token" });
  });

  it("supports raw transport access", async () => {
    const fetchImpl: typeof fetch = async () => jsonResponse({ data: { wrapped: true }, error: null, meta: { page: 1 } });
    const client = new BitcoinBastionClient({ baseUrl: "http://localhost:8000", fetchImpl });
    await expect(client.raw.get("/health/runtime", { raw: true })).resolves.toMatchObject({ meta: { page: 1 } });
  });
});
