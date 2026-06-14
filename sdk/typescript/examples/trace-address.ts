import { BitcoinBastionClient } from "../src/index.js";

const client = new BitcoinBastionClient({ baseUrl: "http://localhost:8000", apiKey: process.env.BASTION_API_KEY });
const report = await client.trace.analyzeAddress("bc1qexamplepublicaddress000000000000000000000");
console.log(report);
