import { BastionAccessAuth, BitcoinBastionClient } from "../src/index.js";

const baseUrl = process.env.BASTION_API_BASE_URL ?? "http://localhost:8000";
const accessPass = process.env.BASTION_ACCESS_PASS;

if (!accessPass) {
  throw new Error("Set BASTION_ACCESS_PASS to a Bastion Access Pass. This is NOT wallet-secret material.");
}

const accessAuth = new BastionAccessAuth({ accessPass, fetchImpl: fetch });
accessAuth.importAccessPass(accessPass);

const client = new BitcoinBastionClient({ baseUrl, accessAuth: { accessPass, fetchImpl: fetch } });
console.log("Imported Bastion Access Pass safely", accessAuth.exportSafeAccessState());
console.log("Client ready", Boolean(client.access));
