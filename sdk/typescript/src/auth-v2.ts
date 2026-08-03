import { BastionSessionExpiredError } from "./errors.js";
import { canonicalJson, generateNonce, sha256Hex } from "./utils/crypto.js";

export type BastionPrincipalType = "bitcoin_wallet_principal" | "lightning_wallet_principal";
export type WalletProofMethod = "bip322" | "legacy_message_signature" | "hardware_wallet" | "air_gapped" | "multisig_quorum";
export type LightningProofMethod = "lnurl_auth";
export type VerificationStrength = "compatibility" | "standard" | "high_assurance" | "sovereign";
export type WalletAuthAction = "register" | "login" | "new_device" | "step_up" | "create_api_key" | "recovery" | "lockdown";
export type PolicyDecision = "allow" | "deny" | "step_up_required" | "upgrade_required" | "quota_exceeded" | "metric_not_allowed" | "revoked" | "expired" | "recovery_required" | "online_check_required";

export interface WalletProofResult { proofMethod: WalletProofMethod; walletIdentifier?: string; signature: string; network: string; scriptType?: string; metadata?: Record<string, unknown> }
/** External wallet boundary. The Bitcoin Bastion SDK never needs your Bitcoin seed or wallet private key. */
export interface WalletProofSigner {
  readonly kind: WalletProofMethod | (string & {});
  signWalletIntent(input: { intent: string; network: string; action: WalletAuthAction }): Promise<WalletProofResult>;
}
export interface LnurlAuthPresentation { challengeId: string; lnurl: string; action: "register" | "login" | "link" | "auth"; expiresAt: string; domain: string }
export interface LnurlAuthProof { key: string; signature: string; action: "register" | "login" | "link" | "auth" }
export interface LnurlWalletAdapter {
  openAuth?(request: LnurlAuthPresentation): Promise<void>;
  signAuth?(request: LnurlAuthPresentation): Promise<LnurlAuthProof>;
  openPay?(request: LnurlPayRequest): Promise<void>;
  openWithdraw?(request: LnurlWithdrawRequest): Promise<void>;
}
export interface BastionPopSigner { readonly keyId?: string; readonly publicKeyFingerprint: string; sign(input: Uint8Array): Promise<string> }
export interface BastionPopSession { sessionId?: string; sessionToken: string; principalHash: string; principalType: BastionPrincipalType; expiresAt: string; scopes: string[]; plan?: string; policyMode?: string }
export interface BastionPrincipalMetadata { principalHash: string; principalType: BastionPrincipalType; status?: string; verificationStrength?: VerificationStrength }
export interface BastionCanonicalRequest { method: string; path: string; query?: Record<string, unknown>; serializedBody: string; timestamp?: string; nonce?: string }
export interface BastionAuthProvider { getPrincipal?(): BastionPrincipalMetadata | undefined; getSession?(): BastionPopSession | undefined; signRequest?(request: BastionCanonicalRequest): Promise<Record<string, string>>; clearSession?(): void | Promise<void> }
export interface BastionAuthStorage { load(): Promise<BastionPopSession | undefined>; save(session: BastionPopSession): Promise<void>; clear(): Promise<void> }

export type LnurlPaymentState = "created" | "invoice_issued" | "pending" | "settled" | "verified" | "expired" | "failed";
export type LnurlSuccessAction = { tag: "message"; message: string } | { tag: "url"; description: string; url: string };
export interface LnurlPayerDataRequest { auth?: { mandatory?: boolean }; identifier?: { mandatory?: boolean }; pubkey?: { mandatory?: boolean }; name?: { mandatory?: boolean }; email?: { mandatory?: boolean } }
export interface LnurlPayRequest { paymentId: string; lnurl?: string; callback?: string; amountMsat?: number; plan?: string; expiresAt?: string; commentAllowed?: number; payerData?: LnurlPayerDataRequest }
export interface LnurlPaymentStatus { paymentId: string; state: LnurlPaymentState; settled: boolean; verifiedAt?: string; paymentProofReference?: string; entitlementReference?: string; entitlementActive: boolean; successAction?: LnurlSuccessAction }
export interface LnurlWithdrawRequest { withdrawId?: string; lnurl?: string; callback?: string; expiresAt?: string; minWithdrawable?: number; maxWithdrawable?: number; policyApproved?: boolean }
export interface LnurlWithdrawStatus { withdrawId: string; status: "created" | "pending" | "paid" | "expired" | "failed" | "cancelled"; payoutComplete: boolean }
export interface LightningAddressDescriptor { address: string; username: string; domain: string }

export function canonicalizeQuery(query?: Record<string, unknown>): string {
  const pairs: Array<[string, string]> = [];
  for (const [key, value] of Object.entries(query ?? {})) {
    if (value === undefined || value === null) continue;
    if (Array.isArray(value)) for (const item of value) pairs.push([key, String(item)]); else pairs.push([key, String(value)]);
  }
  pairs.sort(([ak, av], [bk, bv]) => ak.localeCompare(bk) || av.localeCompare(bv));
  return pairs.map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`).join("&");
}
export function hashRequestBody(serializedBody: string): string { return sha256Hex(serializedBody); }
export function canonicalizeRequest(input: Required<Pick<BastionCanonicalRequest, "method" | "path" | "serializedBody">> & Pick<BastionCanonicalRequest, "query"> & { timestamp: string; nonce: string }): string {
  if (!input.path.startsWith("/") || input.path.includes("?") || input.path.includes("#")) throw new Error("path must be absolute and exclude query/fragment");
  const query = canonicalizeQuery(input.query);
  const target = query ? `${input.path}?${query}` : input.path;
  return [input.method.toUpperCase(), target, hashRequestBody(input.serializedBody), input.timestamp, input.nonce].join("\n");
}
export function buildPopSigningPayload(input: Parameters<typeof canonicalizeRequest>[0]): Uint8Array { const hex = sha256Hex(canonicalizeRequest(input)); return Uint8Array.from(hex.match(/../g) ?? [], byte => Number.parseInt(byte, 16)); }

/** In-memory-only PoP provider; persistence is exclusively application controlled. */
export class WalletLnurlAuthProvider implements BastionAuthProvider {
  private session?: BastionPopSession;
  constructor(private readonly signer: BastionPopSigner, session?: BastionPopSession, private readonly clock: () => Date = () => new Date(), private readonly nonce: () => string = generateNonce) { this.session = session; }
  setSession(session: BastionPopSession): void { this.session = { ...session, scopes: [...session.scopes] }; }
  getSession(): BastionPopSession | undefined { return this.session; }
  getSessionMetadata(): Omit<BastionPopSession, "sessionToken"> | undefined { if (!this.session) return undefined; const { sessionToken: _, ...safe } = this.session; return safe; }
  isSessionExpired(): boolean { return !this.session || Date.parse(this.session.expiresAt) <= this.clock().getTime(); }
  clearSession(): void { this.session = undefined; }
  async signRequest(request: BastionCanonicalRequest): Promise<Record<string, string>> {
    if (!this.session) throw new BastionSessionExpiredError("A Device-bound PoP Session is required.");
    if (this.isSessionExpired()) throw new BastionSessionExpiredError("PoP Session is expired.");
    const timestamp = request.timestamp ?? this.clock().toISOString();
    const nonce = request.nonce ?? this.nonce();
    const bodyHash = hashRequestBody(request.serializedBody);
    const signature = await this.signer.sign(buildPopSigningPayload({ ...request, timestamp, nonce }));
    return { Authorization: `PoP ${this.session.sessionToken}`, "Bastion-Request-Timestamp": timestamp, "Bastion-Request-Nonce": nonce, "Bastion-Request-Body-Hash": bodyHash, "Bastion-Request-Signature": signature, "Bastion-Principal": this.session.principalHash };
  }
}

export function serializeRequestBody(body: unknown): string { return body === undefined ? "" : canonicalJson(body); }
