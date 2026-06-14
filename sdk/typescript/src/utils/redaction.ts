const SECRET_KEYS = ["secret", "token", "authorization", "api_key", "signature", "private_key"];

export function redactSensitive(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(redactSensitive);
  if (value && typeof value === "object") {
    const result: Record<string, unknown> = {};
    for (const [key, item] of Object.entries(value)) {
      result[key] = SECRET_KEYS.some((needle) => key.toLowerCase().includes(needle))
        ? "[REDACTED]"
        : redactSensitive(item);
    }
    return result;
  }
  return value;
}
