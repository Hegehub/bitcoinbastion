import { BitcoinBastionClient } from "../src/index.js";
const client = new BitcoinBastionClient({ baseUrl: "https://api.example.test" });
const payment = await client.lnurlPay.createSubscriptionPayment({ plan: "pro_pass" });
console.info(payment.lnurl); // Invoice issuance is not settlement.
const verified = await client.lnurlPay.verifyPayment(payment.paymentId);
if (!verified.settled) throw new Error("Payment is not backend-verified as settled.");
