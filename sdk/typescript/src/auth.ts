import {
  AccessAuthRequiredError,
  AccessChallengeError,
  AccessLegacyAuthDisabledError,
  AccessSessionExpiredError,
  AccessSigningError,
} from "./errors.js";
import {
  bodyHash,
  buildRequestDigest,
  generateNonce,
  nowIsoTimestamp,
} from "./utils/crypto.js";
import { redactAccessPass, redactSensitiveObject, redactSessionToken } from "./utils/redaction.js";

export const LEGACY_AUTH_DISABLED_MESSAGE =
  "Legacy auth is disabled. Use Proof-of-Access challenge/session flow.";

export class LegacyAuthDisabledError extends AccessLegacyAuthDisabledError {
  constructor() {
    super(LEGACY_AUTH_DISABLED_MESSAGE);
    this.name = "LegacyAuthDisabledError";
  }
}

export interface BastionAccessPassImport {
  accessPass?: string;
  certificateFingerprint?: string;
  metadata?: Record<string, unknown>;
}

export interface BastionAccessChallengeRequest {
  origin?: string;
  requestedScopes?: string[];
  certificateFingerprint?: string;
  deviceKeyFingerprint?: string;
}

export interface BastionAccessChallengeResponse {
  challengeId: string;
  challengePayload: string;
  expiresAt: string;
  requestedScopes: string[];
  origin: string;
}

export interface BastionAccessSession {
  sessionToken: string;
  expiresAt: string;
  scopes: string[];
  planCode: string;
  policyMode?: string;
}

export interface BastionAccessSessionState {
  session: BastionAccessSession | null;
  certificateFingerprint?: string;
  importedPass?: BastionAccessPassImport;
}

export interface AccessSigner {
  getPublicKeyFingerprint(): Promise<string> | string;
  signDigest(digest: string): Promise<string> | string;
}

export interface SignedRequestHeaders extends Record<string, string> {
  "X-Bastion-Session": string;
  "X-Bastion-Timestamp": string;
  "X-Bastion-Nonce": string;
  "X-Bastion-Body-Hash": string;
  "X-Bastion-Signature": string;
  "X-Bastion-Auth-Version": "proof-of-access-v1";
}

export interface BastionAccessAuthConfig {
  accessPass?: string;
  sessionToken?: string;
  sessionExpiresAt?: string;
  sessionScopes?: string[];
  planCode?: string;
  origin?: string;
  deviceKeyProvider?: AccessSigner;
  challengeEndpoint?: string;
  sessionEndpoint?: string;
  clockSkewSeconds?: number;
  legacyBearerToken?: string;
  allowLegacyBearerAuth?: boolean;
  fetchImpl?: typeof fetch;
}

export interface AccessAuthProvider {
  importAccessPass(pass: string): void;
  createChallenge(requestedScopes?: string[]): Promise<BastionAccessChallengeResponse>;
  createSession(challengeSignature: string): Promise<BastionAccessSession>;
  getSession(): BastionAccessSession | null;
  signRequest(method: string, path: string, body?: unknown): Promise<SignedRequestHeaders>;
  clearSession(): void;
}

/** @deprecated Legacy compatibility helper. Proof-of-Access uses a PoP auth provider. */
export function legacyAuthHeaders(
  apiKey?: string,
  options: { allowLegacyBearerAuth?: boolean; warn?: (message: string) => void } = {},
): Record<string, string> {
  void options;
  if (!apiKey) return {};
  throw new LegacyAuthDisabledError();
}

/** @deprecated Use a BastionAuthProvider; retained as a fail-closed source compatibility alias. */
export const authHeaders = legacyAuthHeaders;

export function proofOfAccessHeaders(input: {
  session: string;
  timestamp: string;
  nonce: string;
  bodyHash: string;
  signature: string;
}): Record<string, string> {
  return {
    "X-Bastion-Session": input.session,
    "X-Bastion-Timestamp": input.timestamp,
    "X-Bastion-Nonce": input.nonce,
    "X-Bastion-Body-Hash": input.bodyHash,
    "X-Bastion-Signature": input.signature,
  };
}

export function redactAccessSecret(value: string): string {
  if (value.startsWith("bbk_live_")) return "bbk_live_…redacted";
  if (value.startsWith("bbd_live_")) return "bbd_live_…redacted";
  if (value.startsWith("bap_")) return "bap_…redacted";
  if (value.startsWith("bbp_live_")) return redactAccessPass(value);
  return "<redacted>";
}

export class BastionAccessAuth implements AccessAuthProvider {
  private importedPass?: BastionAccessPassImport;
  private session: BastionAccessSession | null;
  private readonly signer?: AccessSigner;
  private readonly origin: string;
  private readonly challengeEndpoint: string;
  private readonly sessionEndpoint: string;

  constructor(private readonly config: BastionAccessAuthConfig = {}) {
    this.importedPass = config.accessPass ? { accessPass: config.accessPass } : undefined;
    this.session = config.sessionToken
      ? {
          sessionToken: config.sessionToken,
          expiresAt: config.sessionExpiresAt ?? new Date(Date.now() + 15 * 60_000).toISOString(),
          scopes: config.sessionScopes ?? [],
          planCode: config.planCode ?? "unknown",
        }
      : null;
    this.signer = config.deviceKeyProvider;
    this.origin = config.origin ?? "https://app.bitcoinbastion.local";
    this.challengeEndpoint = config.challengeEndpoint ?? "/access/challenges";
    this.sessionEndpoint = config.sessionEndpoint ?? "/access/sessions";
  }

  importAccessPass(pass: string): void {
    this.importedPass = { accessPass: pass };
  }

  async createChallenge(requestedScopes: string[] = []): Promise<BastionAccessChallengeResponse> {
    if (!this.importedPass?.accessPass && !this.importedPass?.certificateFingerprint) {
      throw new AccessChallengeError("Access Pass or certificate fingerprint is required to create a challenge.");
    }
    if (!this.config.fetchImpl) {
      throw new AccessChallengeError("Access challenge helper requires fetchImpl in BastionAccessAuthConfig.");
    }
    const deviceKeyFingerprint = this.signer
      ? await this.signer.getPublicKeyFingerprint()
      : undefined;
    const response = await this.config.fetchImpl(this.challengeEndpoint, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        access_pass: this.importedPass.accessPass,
        certificate_fingerprint: this.importedPass.certificateFingerprint,
        origin: this.origin,
        requested_scopes: requestedScopes,
        device_key_fingerprint: deviceKeyFingerprint,
      }),
    });
    const payload = (await response.json()) as Record<string, unknown>;
    const data = ("data" in payload ? payload.data : payload) as Record<string, unknown>;
    return {
      challengeId: String(data.challenge_id ?? data.challengeId),
      challengePayload: String(data.challenge_payload ?? data.challengePayload),
      expiresAt: String(data.expires_at ?? data.expiresAt),
      requestedScopes: (data.requested_scopes ?? data.requestedScopes ?? []) as string[],
      origin: String(data.origin ?? this.origin),
    };
  }

  async createSession(challengeSignature: string): Promise<BastionAccessSession> {
    if (!this.config.fetchImpl) {
      throw new AccessChallengeError("Access session helper requires fetchImpl in BastionAccessAuthConfig.");
    }
    const response = await this.config.fetchImpl(this.sessionEndpoint, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ signature: challengeSignature }),
    });
    const payload = (await response.json()) as Record<string, unknown>;
    const data = ("data" in payload ? payload.data : payload) as Record<string, unknown>;
    this.session = {
      sessionToken: String(data.session_token ?? data.sessionToken),
      expiresAt: String(data.expires_at ?? data.expiresAt),
      scopes: (data.scopes ?? []) as string[],
      planCode: String(data.plan_code ?? data.planCode),
      policyMode: data.policy_mode ? String(data.policy_mode) : undefined,
    };
    return this.session;
  }

  getSession(): BastionAccessSession | null {
    return this.session;
  }

  clearSession(): void {
    this.session = null;
  }

  async signRequest(method: string, path: string, body?: unknown): Promise<SignedRequestHeaders> {
    if (!this.session) throw new AccessAuthRequiredError();
    if (Date.parse(this.session.expiresAt) <= Date.now()) {
      throw new AccessSessionExpiredError();
    }
    if (!this.signer) throw new AccessSigningError("Access signer is required for Proof-of-Access requests.");
    const timestamp = nowIsoTimestamp();
    const nonce = generateNonce();
    const hashedBody = bodyHash(body);
    const digest = buildRequestDigest({ method, path, bodyHash: hashedBody, timestamp, nonce });
    const signature = await this.signer.signDigest(digest);
    return {
      "X-Bastion-Session": this.session.sessionToken,
      "X-Bastion-Timestamp": timestamp,
      "X-Bastion-Nonce": nonce,
      "X-Bastion-Body-Hash": hashedBody,
      "X-Bastion-Signature": signature,
      "X-Bastion-Auth-Version": "proof-of-access-v1",
    };
  }

  exportSafeAccessState(): unknown {
    return redactSensitiveObject({
      importedPass: this.importedPass
        ? { ...this.importedPass, accessPass: this.importedPass.accessPass ? redactAccessPass(this.importedPass.accessPass) : undefined }
        : undefined,
      session: this.session
        ? { ...this.session, sessionToken: redactSessionToken(this.session.sessionToken) }
        : null,
    });
  }
}
