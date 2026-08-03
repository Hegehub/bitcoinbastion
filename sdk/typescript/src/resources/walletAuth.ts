import type { WalletAuthAction, WalletProofResult } from "../auth-v2.js";
import type { BastionHttpClient } from "../http.js";
import { assertNoWalletSecretFields } from "../safety.js";

export interface WalletChallengeRequest { action: WalletAuthAction; network: string; proofType: string; origin: string; deviceKeyFingerprint?: string; requestedScopes?: string[] }
export interface WalletChallenge { challengeId: string; canonicalIntent: string; intentHash: string; expiresAt: string; network: string; proofType: string; safetyWarning: string }
export class WalletAuthResource {
  constructor(private readonly http: BastionHttpClient) {}
  createChallenge(input: WalletChallengeRequest): Promise<WalletChallenge> { assertNoWalletSecretFields(input); return this.http.post("/wallet-auth/challenges", snake(input)); }
  register(input: { challengeId: string; proof: WalletProofResult; device: Record<string, unknown> }): Promise<unknown> { assertNoWalletSecretFields(input); return this.http.post("/wallet-auth/register", snake(input)); }
  login(input: { challengeId: string; proof: WalletProofResult; deviceKeyFingerprint?: string }): Promise<unknown> { assertNoWalletSecretFields(input); return this.http.post("/wallet-auth/login", snake(input)); }
  createSession(input: Record<string, unknown>): Promise<unknown> { assertNoWalletSecretFields(input); return this.http.post("/wallet-auth/sessions", snake(input)); }
  stepUp(input: Record<string, unknown>): Promise<unknown> { assertNoWalletSecretFields(input); return this.http.post("/wallet-auth/step-up", snake(input), { requireAuth: true }); }
  getPrincipal(): Promise<unknown> { return this.http.get("/wallet-auth/me", { requireAuth: true }); }
  getEntitlements(): Promise<unknown> { return this.http.get("/wallet-auth/entitlements", { requireAuth: true }); }
  listDevices(): Promise<unknown> { return this.http.get("/wallet-auth/devices", { requireAuth: true }); }
  revokeDevice(id: string): Promise<unknown> { return this.http.delete(`/wallet-auth/devices/${encodeURIComponent(id)}`, { requireAuth: true }); }
  listWallets(): Promise<unknown> { return this.http.get("/wallet-auth/wallets", { requireAuth: true }); }
  startRecovery(input: Record<string, unknown>): Promise<unknown> { assertNoWalletSecretFields(input); return this.http.post("/wallet-auth/recovery/start", snake(input)); }
  getRecoveryStatus(id: string): Promise<unknown> { return this.http.get(`/wallet-auth/recovery/${encodeURIComponent(id)}`); }
  submitRecoveryFactor(id: string, input: Record<string, unknown>): Promise<unknown> { assertNoWalletSecretFields(input); return this.http.post(`/wallet-auth/recovery/${encodeURIComponent(id)}/factor`, snake(input)); }
  completeRecovery(id: string, input: Record<string, unknown>): Promise<unknown> { assertNoWalletSecretFields(input); return this.http.post(`/wallet-auth/recovery/${encodeURIComponent(id)}/complete`, snake(input)); }
  startLockdown(input: Record<string, unknown>): Promise<unknown> { return this.http.post("/wallet-auth/lockdown", snake(input), { requireAuth: true }); }
  getLockdownStatus(recoveryReference?: string): Promise<unknown> { return this.http.get("/wallet-auth/lockdown/status", { query: { recovery_reference: recoveryReference } }); }
}
function snake(value: object): Record<string, unknown> { return Object.fromEntries(Object.entries(value).map(([k, v]) => [k.replace(/[A-Z]/g, x => `_${x.toLowerCase()}`), v])); }
