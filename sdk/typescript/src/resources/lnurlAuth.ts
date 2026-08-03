import type { LnurlAuthPresentation, LnurlWalletAdapter } from "../auth-v2.js";
import type { BastionHttpClient } from "../http.js";
import { assertNoWalletSecretFields } from "../safety.js";

export class LnurlAuthResource {
  constructor(private readonly http: BastionHttpClient, private readonly expectedDomain?: string) {}
  async createChallenge(input: Record<string, unknown>): Promise<LnurlAuthPresentation> {
    assertNoWalletSecretFields(input);
    const raw = await this.http.post<Record<string, unknown>>("/lnurl/auth/challenges", input);
    const result = { challengeId: String(raw.challenge_id), lnurl: String(raw.lnurl ?? raw.lnurl_bech32), action: String(raw.action) as LnurlAuthPresentation["action"], expiresAt: String(raw.expires_at), domain: String(raw.auth_domain ?? raw.domain) };
    if (this.expectedDomain && result.domain !== this.expectedDomain) throw new Error("LNURL-auth domain mismatch.");
    return result;
  }
  createSession(input: Record<string, unknown>): Promise<unknown> { return this.http.post("/lnurl/auth/sessions", input); }
  stepUp(input: Record<string, unknown>): Promise<unknown> { return this.http.post("/lnurl/auth/step-up", input, { requireAuth: true }); }
  async open(challenge: LnurlAuthPresentation, adapter: LnurlWalletAdapter): Promise<void> { if (!adapter.openAuth) throw new Error("LNURL wallet adapter does not support openAuth."); await adapter.openAuth(challenge); }
}
