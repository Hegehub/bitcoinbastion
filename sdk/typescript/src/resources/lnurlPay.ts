import type { LnurlPaymentStatus, LnurlPayRequest } from "../auth-v2.js";
import type { BastionHttpClient } from "../http.js";
import { BastionPaymentNotSettledError } from "../errors.js";

export class LnurlPayResource {
  constructor(private readonly http: BastionHttpClient) {}
  async createSubscriptionPayment(input: { plan: string; durationDays?: number; commentAllowed?: number; payerdataAuthRequested?: boolean; successActionRequested?: boolean }): Promise<LnurlPayRequest> {
    const raw = await this.http.post<Record<string, unknown>>("/lnurl/pay/subscriptions", { plan_code: input.plan, duration_days: input.durationDays, comment_allowed: input.commentAllowed, payerdata_auth_requested: input.payerdataAuthRequested, success_action_requested: input.successActionRequested });
    return { paymentId: String(raw.payment_id), lnurl: stringOr(raw.lnurl, raw.lnurl_bech32), callback: stringOr(raw.callback), plan: input.plan, expiresAt: stringOr(raw.expires_at), commentAllowed: numberOr(raw.comment_allowed) };
  }
  requestInvoice(paymentId: string, amountMsat: number, comment?: string, commentAllowed?: number): Promise<unknown> { if (comment !== undefined && commentAllowed !== undefined && [...comment].length > commentAllowed) throw new Error("LNURL comment exceeds commentAllowed."); return this.http.get(`/lnurl/pay/callback/${encodeURIComponent(paymentId)}`, { query: { amount: amountMsat, comment }, raw: true }); }
  async verifyPayment(paymentId: string): Promise<LnurlPaymentStatus> {
    const raw = await this.http.get<Record<string, unknown>>(`/lnurl/pay/verify/${encodeURIComponent(paymentId)}`, { raw: true });
    const settled = raw.settled === true;
    const state = String(raw.payment_state ?? raw.state ?? raw.status ?? (settled ? "verified" : "pending")) as LnurlPaymentStatus["state"];
    return { paymentId, state, settled, verifiedAt: stringOr(raw.verified_at), paymentProofReference: stringOr(raw.payment_proof_hash), entitlementReference: stringOr(raw.entitlement_hash), entitlementActive: settled && raw.entitlement_active === true };
  }
  async requireSettled(paymentId: string): Promise<LnurlPaymentStatus> { const status = await this.verifyPayment(paymentId); if (!status.settled) throw new BastionPaymentNotSettledError({ message: "Backend has not verified LNURL payment settlement." }); return status; }
}
function stringOr(...values: unknown[]): string | undefined { const value = values.find(v => typeof v === "string"); return value as string | undefined; }
function numberOr(value: unknown): number | undefined { return typeof value === "number" ? value : undefined; }
