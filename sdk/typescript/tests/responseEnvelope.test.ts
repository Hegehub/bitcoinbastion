import { describe, expect, it } from "vitest";
import { BitcoinBastionClient } from "../src/index.js";

const response = (body: unknown) => new Response(JSON.stringify(body), { status: 200 });

describe("ResponseEnvelope handling", () => {
  it("unwraps data by default", async () => {
    const client = new BitcoinBastionClient({ baseUrl: "http://localhost:8000", fetchImpl: async () => response({ data: { value: 1 }, error: null }) });
    await expect(client.providerHealth.status()).resolves.toEqual({ value: 1 });
  });

  it("handles plain payloads", async () => {
    const client = new BitcoinBastionClient({ baseUrl: "http://localhost:8000", fetchImpl: async () => response({ value: 2 }) });
    await expect(client.providerHealth.status()).resolves.toEqual({ value: 2 });
  });
});
