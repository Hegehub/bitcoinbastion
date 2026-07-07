import { BitcoinBastionClient } from "../src/index.js";

const client = new BitcoinBastionClient({ baseUrl: process.env.BASTION_API_BASE_URL ?? "http://localhost:8000" });
const address = process.env.BASTION_TRACE_ADDRESS ?? "bc1qexamplepublicaddress000000000000000000000";

// Public trace-lite calls do not require Proof-of-Access. Never enter a Bitcoin seed/private key; reject wallet-secret input here.
console.log(await client.trace.getLite(address));
