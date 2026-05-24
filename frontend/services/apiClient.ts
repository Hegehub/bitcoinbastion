import { ApiEnvelope, PublicStatusDTO, RuntimeEventDTO } from '@/types/api'
import { normalizeApiError } from './api'

async function get<T>(path: string): Promise<T> {
  const ctl = new AbortController()
  const to = setTimeout(() => ctl.abort(), 5000)
  try {
    const r = await fetch(path, { signal: ctl.signal })
    const body = (await r.json()) as ApiEnvelope<T>
    if (!r.ok) throw new Error(body.error?.code || `api_error_${r.status}`)
    return (body.data ?? (body as unknown as T))
  } catch (e) {
    throw new Error(normalizeApiError(e))
  } finally { clearTimeout(to) }
}

export const apiClient = {
  getPublicLanding: () => get<object>('/api/v1/public/landing'),
  getPublicStatus: () => get<PublicStatusDTO>('/api/v1/public/status'),
  checkTraceLite: (address: string) => get<{ report_id: number }>(`/api/v1/trace/lite/${address}`),
  getTraceSummary: (reportId: number) => get<object>(`/api/v1/public/trace/${reportId}/summary`),
  getTraceReport: (reportId: number) => get<object>(`/api/v1/trace/report/${reportId}`),
  getProofPacket: (reportId: number) => get<object>(`/api/v1/trace/report/${reportId}/proof-packet`),
  getTraceStatus: () => get<object>('/api/v1/trace/status'),
  getRuntimeEvents: () => get<RuntimeEventDTO[]>('/api/v1/trace/events'),
}
