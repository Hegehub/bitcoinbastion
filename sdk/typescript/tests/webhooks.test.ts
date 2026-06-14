import { createHmac } from "node:crypto";
import { describe, expect, it } from "vitest";
import { BitcoinBastionClient, verifyBastionWebhookSignature } from "../src/index.js";

describe("webhooks", () => {
  it("creates webhook through expected endpoint", async () => {
    let url = "";
    let body = "";
    const client = new BitcoinBastionClient({
      baseUrl: "http://localhost:8000",
      fetchImpl: async (input, init) => {
        url = String(input);
        body = String(init?.body);
        return new Response(JSON.stringify({ data: { id: 1 }, error: null }), { status: 201 });
      },
    });
    await client.webhooks.create({ url: "https://example.com/hook", events: ["signal.published"] });
    expect(url).toContain("/api/v1/webhooks");
    expect(body).toContain("target_url");
  });

  it("verifies webhook signatures", () => {
    const payload = "{\"ok\":true}";
    const timestamp = Math.floor(Date.now() / 1000);
    const secret = "whsec_test_secret";
    const deliveryId = "whd_test";
    const eventType = "signal.published";
    const signature = `v1=${createHmac("sha256", secret).update(`${timestamp}.${deliveryId}.${eventType}.${payload}`).digest("hex")}`;
    expect(verifyBastionWebhookSignature({ payload, timestamp, secret, signature, deliveryId, eventType })).toBe(true);
    expect(verifyBastionWebhookSignature({ payload, timestamp, secret: "wrong", signature, deliveryId, eventType })).toBe(false);
  });
});
