import { BitcoinBastionClient } from "../src/index.js";

const client = new BitcoinBastionClient({ baseUrl: process.env.BASTION_API_BASE_URL ?? "http://localhost:8000" });

// Public/latest signals can be queried without Access Auth when the API exposes them publicly.
console.log(await client.signals.latest());
