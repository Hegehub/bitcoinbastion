import { BastionSafetyError } from "./errors.js";

const SENSITIVE_PATTERNS = [
  "seed phrase",
  "mnemonic",
  "private key",
  "bitcoin seed",
  "wallet seed",
  "xprv",
  "yprv",
  "zprv",
  "wallet.dat",
  "keystore",
  "12 words",
  "24 words",
  "signing material",
  "bitcoin_seed",
  "private_key",
];

export const SAFETY_MESSAGE =
  "Never submit seed phrases, private keys, wallet files, xprv/yprv/zprv, or signing material to Bitcoin Bastion.";

export function containsSensitiveMaterial(value: unknown): boolean {
  return SENSITIVE_PATTERNS.some((pattern) => flatten(value).toLowerCase().includes(pattern));
}

export function assertNoSensitiveMaterial(value: unknown): void {
  if (containsSensitiveMaterial(value)) throw new BastionSafetyError(SAFETY_MESSAGE);
}

function flatten(value: unknown): string {
  if (typeof value === "string") return value;
  if (Array.isArray(value)) return value.map(flatten).join(" ");
  if (value && typeof value === "object") return Object.entries(value).map(([key, item]) => `${key} ${flatten(item)}`).join(" ");
  return String(value ?? "");
}
