const ETH = /^0x[a-fA-F0-9]{40}$/
const BTC = /^(1|3)[a-km-zA-HJ-NP-Z1-9]{25,34}$|^(bc1)[a-z0-9]{11,71}$/
const XPRV = /^(xprv|tprv|xpriv)/i
const WIF = /^[5KL][1-9A-HJ-NP-Za-km-z]{50,51}$/

export function validatePublicBitcoinAddress(input: string): { valid: boolean; error?: string } {
  const value = input.trim()
  if (!value) return { valid: false, error: 'Enter a public Bitcoin address.' }
  if (ETH.test(value) || XPRV.test(value) || WIF.test(value) || value.split(/\s+/).length >= 12 || value.includes('.dat')) {
    return { valid: false, error: 'Sensitive wallet material is not accepted. Only public Bitcoin addresses are supported.' }
  }
  if (!BTC.test(value)) return { valid: false, error: 'Enter a valid public Bitcoin address.' }
  return { valid: true }
}
