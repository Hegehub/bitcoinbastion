import type { LightningAddressDescriptor } from "../auth-v2.js";
export class LightningAddressResource {
  parse(address: string): LightningAddressDescriptor { const normalized = address.trim().toLowerCase(); const parts = normalized.split("@"); if (parts.length !== 2 || !parts[0] || !parts[1] || parts[1].includes("/")) throw new Error("Invalid Lightning Address."); return { address: normalized, username: parts[0], domain: parts[1] }; }
  discoveryUrl(address: string): string { const parsed = this.parse(address); return `https://${parsed.domain}/.well-known/lnurlp/${encodeURIComponent(parsed.username)}`; }
}
