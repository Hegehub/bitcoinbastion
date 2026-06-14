import { apiClient } from '@/services/apiClient'
import { apiGet } from '@/services/api'
import { vi } from 'vitest'

function mockFetch(data: unknown, ok = true, status = 200) {
  vi.stubGlobal('fetch', vi.fn(async () => ({ ok, status, json: async () => data })) as any)
}

test('Trace API client methods use implemented backend endpoints', async () => {
  mockFetch({ success: true, data: { report_id: 1, evidence_refs: [], limitations: [], advisory_only: true, not_legal_verification: true, not_bitcoin_consensus_proof: true, no_custody: true, signed: false, signature_available: false, signature_status: 'unsigned', packet_type: 'application_level_evidence_summary' } })

  await apiClient.checkTraceLite('bc1qxy')
  await apiClient.getTraceSummary(1)
  await apiClient.getTraceReport(1)
  await apiClient.getTraceEvidence(1)
  await apiClient.getTracePrivacyShield(1)
  await apiClient.getTraceOriginPassport(1)
  await apiClient.getTraceProviderDisagreement(1)
  await apiClient.getTraceCounterpartyLens(1)
  await apiClient.getTracePolicyFacts(1)
  await apiClient.getProofPacket(1)
  await apiClient.getTraceStatus()
  await apiClient.getTraceEvents()

  const paths = (fetch as any).mock.calls.map((call: unknown[]) => call[0])
  expect(paths).toEqual([
    '/api/v1/trace/lite/bc1qxy',
    '/api/v1/public/trace/1/summary',
    '/api/v1/trace/report/1',
    '/api/v1/trace/report/1/evidence',
    '/api/v1/trace/report/1/privacy-shield',
    '/api/v1/trace/report/1/origin-passport',
    '/api/v1/trace/report/1/provider-disagreement',
    '/api/v1/trace/report/1/counterparty-lens',
    '/api/v1/trace/report/1/policy-facts',
    '/api/v1/trace/report/1/proof-packet',
    '/api/v1/trace/status',
    '/api/v1/trace/events',
  ])
})

test('ResponseEnvelope data unwrap is preserved', async () => {
  mockFetch({ success: true, data: { report_id: 7 } })
  await expect(apiClient.checkTraceLite('bc1qxy')).resolves.toEqual({ report_id: 7 })
  await expect(apiGet<{ report_id: number }>('/api/v1/trace/lite/bc1qxy')).resolves.toEqual({ report_id: 7 })
})

test('404 report handling is normalized', async () => {
  mockFetch({ success: false, error: { code: 'api_error_404', message: 'not found' } }, false, 404)
  await expect(apiClient.getTraceSummary(999)).rejects.toThrow(/not found/i)
})

test('timeout/error state is normalized', async () => {
  vi.stubGlobal('fetch', vi.fn(async () => { throw new DOMException('aborted', 'AbortError') }) as any)
  await expect(apiClient.getTraceStatus()).rejects.toThrow(/timed out/i)
})
