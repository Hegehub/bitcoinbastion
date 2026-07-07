import { createHash, randomBytes } from "node:crypto";

export function canonicalJson(value: unknown): string {
  if (value === undefined || value === null) return "";
  return JSON.stringify(sortCanonical(value));
}

function sortCanonical(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(sortCanonical);
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>)
        .sort(([left], [right]) => left.localeCompare(right))
        .map(([key, item]) => [key, sortCanonical(item)]),
    );
  }
  return value;
}

export function sha256Hex(input: string | Uint8Array): string {
  return createHash("sha256").update(input).digest("hex");
}

export function generateNonce(): string {
  return randomBytes(16).toString("hex");
}

export function nowIsoTimestamp(): string {
  return new Date().toISOString();
}

export function bodyHash(body: unknown): string {
  return `sha256:${sha256Hex(canonicalJson(body))}`;
}

export interface RequestDigestInput {
  method: string;
  path: string;
  bodyHash: string;
  timestamp: string;
  nonce: string;
}

export function buildRequestDigest(input: RequestDigestInput): string {
  const canonical = [
    input.method.toUpperCase(),
    input.path,
    input.bodyHash,
    input.timestamp,
    input.nonce,
  ].join("\n");
  return `sha256:${sha256Hex(canonical)}`;
}
