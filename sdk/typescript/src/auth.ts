export const LEGACY_AUTH_DISABLED_MESSAGE = "Legacy auth is disabled. Use Proof-of-Access challenge/session flow.";

export class LegacyAuthDisabledError extends Error {
  constructor() {
    super(LEGACY_AUTH_DISABLED_MESSAGE);
    this.name = "LegacyAuthDisabledError";
  }
}

export function authHeaders(apiKey?: string): Record<string, string> {
  if (apiKey) {
    throw new LegacyAuthDisabledError();
  }
  return {};
}

export interface ProofOfAccessHeaderInput {
  session: string;
  timestamp: string;
  nonce: string;
  bodyHash: string;
  signature: string;
}

export function proofOfAccessHeaders(input: ProofOfAccessHeaderInput): Record<string, string> {
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
  return "<redacted>";
}
