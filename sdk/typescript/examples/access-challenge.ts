import { BitcoinBastionClient } from "../src/index.js";

const baseUrl = process.env.BASTION_API_BASE_URL ?? "http://localhost:8000";
const accessPass = process.env.BASTION_ACCESS_PASS;

if (!accessPass) {
  throw new Error("Set BASTION_ACCESS_PASS. Bastion will never ask for your Bitcoin wallet-secret material; reject wallet-secret input.");
}

const client = new BitcoinBastionClient({ baseUrl });
const challenge = await client.access.createChallenge({
  access_pass: accessPass,
  origin: "https://app.example.com",
  requested_scopes: ["market:intelligence:read"],
});
console.log("Challenge created", { challengeId: challenge.challengeId, origin: challenge.origin });
