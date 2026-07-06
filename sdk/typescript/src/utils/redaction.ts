const SECRET_KEYS = [
  "secret",
  "token",
  "authorization",
  "api_key",
  "apikey",
  "signature",
  "private_key",
  "access_pass",
  "session",
  "x-bastion-session",
  "x-bastion-signature",
];

function redactWithPrefix(value: string, prefix: string): string {
  return value.length <= prefix.length + 4 ? `${prefix}...redacted` : `${prefix}...${value.slice(-4)}`;
}

export function redactAccessPass(value: string): string {
  if (value.startsWith("bbp_live_")) return redactWithPrefix(value, "bbp_live_");
  if (value.startsWith("bap_")) return redactWithPrefix(value, "bap_");
  return "<redacted-access-pass>";
}

export function redactSessionToken(value: string): string {
  if (value.startsWith("sess_")) return redactWithPrefix(value, "sess_");
  return value.length > 4 ? `sess_...${value.slice(-4)}` : "sess_...redacted";
}

export function redactSignature(value: string): string {
  if (value.startsWith("sig_")) return redactWithPrefix(value, "sig_");
  return value.length > 4 ? `sig_...${value.slice(-4)}` : "sig_...redacted";
}

export function redactSensitiveObject(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(redactSensitiveObject);
  if (value && typeof value === "object") {
    const result: Record<string, unknown> = {};
    for (const [key, item] of Object.entries(value)) {
      const lowered = key.toLowerCase();
      if (SECRET_KEYS.some((needle) => lowered.includes(needle))) {
        result[key] = "[REDACTED]";
      } else {
        result[key] = redactSensitiveObject(item);
      }
    }
    return result;
  }
  return value;
}

export const redactSensitive = redactSensitiveObject;
