import { ApiEnvelope, PublicStatusDTO } from '@/types/api'
import { LiteTraceResult, PublicTraceSummary, TraceEvidence, TraceProofPacket, TraceReport, TraceRuntimeEvent, TraceStatus } from '@/types/trace'
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
  checkTraceLite: (address: string) => get<LiteTraceResult>(`/api/v1/trace/lite/${encodeURIComponent(address)}`),
  getTraceSummary: (reportId: number | string) => get<PublicTraceSummary>(`/api/v1/public/trace/${reportId}/summary`),
  getTraceReport: (reportId: number | string) => get<TraceReport>(`/api/v1/trace/report/${reportId}`),
  getTraceEvidence: (reportId: number | string) => get<TraceEvidence[]>(`/api/v1/trace/report/${reportId}/evidence`),
  getTracePrivacyShield: (reportId: number | string) => get<Record<string, unknown>>(`/api/v1/trace/report/${reportId}/privacy-shield`),
  getTraceOriginPassport: (reportId: number | string) => get<Record<string, unknown>>(`/api/v1/trace/report/${reportId}/origin-passport`),
  getTraceProviderDisagreement: (reportId: number | string) => get<Record<string, unknown>>(`/api/v1/trace/report/${reportId}/provider-disagreement`),
  getTraceCounterpartyLens: (reportId: number | string) => get<Record<string, unknown>>(`/api/v1/trace/report/${reportId}/counterparty-lens`),
  getTracePolicyFacts: (reportId: number | string) => get<Record<string, unknown>>(`/api/v1/trace/report/${reportId}/policy-facts`),
  getProofPacket: (reportId: number | string) => get<TraceProofPacket>(`/api/v1/trace/report/${reportId}/proof-packet`),
  getTraceStatus: () => get<TraceStatus>('/api/v1/trace/status'),
  getTraceEvents: () => get<TraceRuntimeEvent[]>('/api/v1/trace/events'),
  getRuntimeEvents: () => get<TraceRuntimeEvent[]>('/api/v1/trace/events'),
}
