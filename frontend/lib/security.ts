export const SECURITY_WARNINGS = [
  'No seed phrases',
  'No private keys',
  'No wallet files',
  'No custody',
  'No transaction signing',
  'No transaction broadcasting',
]

export function hasForbiddenWording(text: string): boolean {
  const s = text.toLowerCase()
  return ['clean address', 'dirty address', 'criminal address', 'guaranteed safe', 'approved payment', 'legally verified', 'compliance certified', 'ai verified', 'production certified'].some((w) => s.includes(w))
}
