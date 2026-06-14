import { BitcoinBastionClient } from "../src/index.js";

const client = new BitcoinBastionClient({ baseUrl: "http://localhost:8000", apiKey: process.env.BASTION_API_KEY });
const webhook = await client.webhooks.create({
  url: "https://example.com/bastion-webhook",
  events: ["signal.published", "trace.report.created", "provider.degraded"],
  description: "Operator notification endpoint",
});
console.log(webhook);
