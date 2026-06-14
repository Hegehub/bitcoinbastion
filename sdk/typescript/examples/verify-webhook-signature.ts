import { verifyBastionWebhookSignature } from "../src/index.js";

const valid = verifyBastionWebhookSignature({
  payload: "{}",
  signature: "v1=example",
  timestamp: Math.floor(Date.now() / 1000),
  secret: "whsec_test_example",
});
console.log(valid);
