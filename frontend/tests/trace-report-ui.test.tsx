import React from 'react'
import { render, waitFor } from '@testing-library/react'
import ReportPage from '../app/trace/[reportId]/page'
import ProofPacketPage from '../app/trace/[reportId]/proof-packet/page'

vi.mock('next/navigation', () => ({ useParams: () => ({ reportId: '1' }) }))
vi.mock('../services/api', () => ({ apiGet: vi.fn(async () => ({ report_id: 1, band: 'HIGH', risk_summary: 'Manual review recommended', privacy_summary: 'Some privacy exposure', origin_summary: 'Unknown origin', confidence_summary: 'Low confidence', manual_review_recommended: true, top_reasons: ['PROVIDER_DISAGREEMENT'], limitations: ['advisory_only'] })) }))

test('report page renders timeline and limitations', async () => {
  const { getByText } = render(<ReportPage />)
  await waitFor(() => getByText(/timeline/i))
  expect(getByText(/not legal verification/i)).toBeTruthy()
})

test('proof packet viewer flags visible', () => {
  const { getByText } = render(<ProofPacketPage params={{ reportId: '1' }} />)
  expect(getByText(/Advisory-only/i)).toBeTruthy()
  expect((document.body.textContent || '').includes('No custody')).toBe(true)
})

test('forbidden wording absent', async () => {
  render(<ReportPage />)
  await waitFor(() => document.body.textContent?.includes('Timeline'))
  const txt = (document.body.textContent || '').toLowerCase()
  for (const bad of ['clean address', 'dirty address', 'criminal address', 'guaranteed safe', 'approved payment', 'verified illicit']) {
    expect(txt.includes(bad)).toBe(false)
  }
})
