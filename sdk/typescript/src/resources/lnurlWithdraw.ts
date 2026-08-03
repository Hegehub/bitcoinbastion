import type { LnurlWalletAdapter, LnurlWithdrawRequest } from "../auth-v2.js";
import type { BastionHttpClient } from "../http.js";
import { assertNoWalletSecretFields } from "../safety.js";
export class LnurlWithdrawResource {
  constructor(private readonly http: BastionHttpClient) {}
  createWithdrawRequest(input: Record<string, unknown>): Promise<LnurlWithdrawRequest> { assertNoWalletSecretFields(input); return this.http.post("/lnurl/withdraw/requests", input, { requireAuth: true }); }
  async openWithdraw(request: LnurlWithdrawRequest, adapter: LnurlWalletAdapter): Promise<void> { if (!adapter.openWithdraw) throw new Error("LNURL wallet adapter does not support openWithdraw."); await adapter.openWithdraw(request); }
}
