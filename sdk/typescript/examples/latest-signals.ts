import { BitcoinBastionClient } from "../src/index.js";

const client = new BitcoinBastionClient({ baseUrl: "http://localhost:8000", apiKey: process.env.BASTION_API_KEY });
const signals = await client.signals.latest({ limit: 10 });
console.log(signals);
