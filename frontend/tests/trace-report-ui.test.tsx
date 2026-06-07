import React from 'react'
import { render, waitFor } from '@testing-library/react'
import ReportPage from '../app/trace/[reportId]/page'
import ProofPacketPage from '../app/trace/[reportId]/proof-packet/page'

const summary = { report_id: 1, band: 'HIGH', risk_summary: 'Manual review recommended', privacy_summary: 'Some privacy exposure', origin_summary: 'Unknown origin', confidence_summary: 'Low confidence', manual_review_recommended: true, top_reasons: ['PROVIDER_DISAGREEMENT'], limitations: ['advisory_only'], safety_warnings: ['Advisory only'] }
const packet = { report_id: 1, advisory_only: true, not_legal_verification: true, not_bitcoin_consensus_proof: true, no_custody: true, signed: false, signature_available: false, signature_status: 'unsigned', packet_type: 'application_level_evidence_summary', evidence_refs: [{ evidence_ref: 'trace:1:baseline' }], limitations: ['Proof packet is an application-level evidence summary.', 'This is not Bitcoin consensus proof.', 'This is not legal verification.'] }

vi.mock('next/navigation', () => ({ useParams: () => ({ reportId: '1' }) }))
vi.mock('../services/apiClient', () => ({ apiClient: { getTraceSummary: vi.fn(async () => summary), getProofPacket: vi.fn(async () => packet) } }))

test('report page renders timeline and limitations', async () => {
  const { getByText } = render(<ReportPage />)
  await waitFor(() => getByText(/timeline/i))
  expect(getByText(/not legal verification/i)).toBeTruthy()
  expect(document.body.textContent || '').toMatch(/Not Bitcoin consensus proof/i)
  expect(getByText(/No custody/i)).toBeTruthy()
})

test('proof packet viewer renders truthful unsigned application-level state', async () => {
  const { getByText } = render(<ProofPacketPage params={{ reportId: '1' }} />)
  await waitFor(() => getByText(/Unsigned application-level evidence summary/i))
  expect(getByText(/Advisory-only/i)).toBeTruthy()
  expect((document.body.textContent || '').includes('No custody')).toBe(true)
  expect(document.body.textContent || '').toMatch(/Not Bitcoin consensus proof/i)
  expect(getByText(/Signature available: no/i)).toBeTruthy()
  expect(getByText(/trace:1:baseline/i)).toBeTruthy()
})

test('forbidden wording absent', async () => {
  render(<ReportPage />)
  await waitFor(() => document.body.textContent?.includes('Timeline'))
  const txt = (document.body.textContent || '').toLowerCase()
  for (const bad of ['clean address', 'dirty address', 'criminal address', 'guaranteed safe', 'approved payment', 'verified illicit']) {
    expect(txt.includes(bad)).toBe(false)
  }
})
