import { describe, expect, it } from "vitest";
import { BitcoinBastionClient, BastionSafetyError } from "../src/index.js";

function ok(): Response { return new Response(JSON.stringify({ data: { reportId: 1 }, error: null }), { status: 200 }); }

describe("TraceResource", () => {
  it("calls the address endpoint", async () => {
    let url = "";
    const client = new BitcoinBastionClient({ baseUrl: "http://localhost:8000", fetchImpl: async (input) => { url = String(input); return ok(); } });
    await client.trace.analyzeAddress("bc1qexamplepublicaddress000000000000000000000");
    expect(url).toContain("/api/v1/trace/address/bc1qexample");
  });

  it("rejects sensitive material before request", async () => {
    let called = false;
    const client = new BitcoinBastionClient({ baseUrl: "http://localhost:8000", fetchImpl: async () => { called = true; return ok(); } });
    expect(() => client.trace.batch(["xprv private key"])).toThrow(BastionSafetyError);
    expect(called).toBe(false);
  });
});
