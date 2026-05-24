export function normalizeApiError(error: unknown): string {
  const msg = error instanceof Error ? error.message : 'api_error_unknown'
  if (msg.includes('api_error_404')) return 'Requested data was not found.'
  if (msg.includes('api_error_422') || msg.includes('api_error_400')) return 'Input is invalid. Please review and retry.'
  if (msg.includes('api_error_429')) return 'Too many requests. Please wait and try again.'
  if (msg.includes('AbortError')) return 'Request timed out. Please retry.'
  return 'Service is temporarily unavailable. Please retry shortly.'
}

export async function apiGet<T>(path: string): Promise<T> {
  const ctl = new AbortController()
  const to = setTimeout(() => ctl.abort(), 5000)
  try {
    const r = await fetch(path, { signal: ctl.signal })
    if (!r.ok) throw new Error(`api_error_${r.status}`)
    const j = await r.json()
    return j.data as T
  } finally {
    clearTimeout(to)
  }
}
