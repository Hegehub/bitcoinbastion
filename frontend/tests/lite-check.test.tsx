import React from 'react'
import { fireEvent, render, waitFor } from '@testing-library/react'
import CheckPage from '../app/check/page'
import { validatePublicBitcoinAddress } from '../lib/addressValidation'

vi.mock('../services/api', () => ({
  apiGet: vi.fn(async (path: string) => {
    if (path.startsWith('/api/v1/trace/lite/')) return { report_id: 1 }
    return { report_id: 1, band: 'MEDIUM', risk_summary: 'Caution', privacy_summary: 'Some privacy exposure', origin_summary: 'Unknown origin', confidence_summary: 'Low confidence', manual_review_recommended: true, top_reasons: ['BASELINE_SCORING_ONLY'], limitations: ['advisory_only'], safety_warnings: ['Advisory only'] }
  })
}))

test('address form renders and keyboard submit works', async () => {
  const { getByLabelText, getByRole, getByText } = render(<CheckPage />)
  const input = getByLabelText('Bitcoin address input') as HTMLInputElement
  fireEvent.change(input, { target: { value: 'bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh' } })
  fireEvent.submit(getByRole('button', { name: 'Submit address check' }).closest('form')!)
  await waitFor(() => getByText(/Risk summary/i))
})

test('ethereum and sensitive inputs rejected', () => {
  expect(validatePublicBitcoinAddress('0x1234567890123456789012345678901234567890').valid).toBe(false)
  expect(validatePublicBitcoinAddress('xprv9s21ZrQH143K3').valid).toBe(false)
  expect(validatePublicBitcoinAddress('abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about').valid).toBe(false)
})

test('forbidden wording absent', () => {
  const { container } = render(<CheckPage />)
  const txt = container.textContent?.toLowerCase() || ''
  for (const bad of ['clean address', 'dirty address', 'guaranteed safe', 'approved payment', 'criminal address']) {
    expect(txt.includes(bad)).toBe(false)
  }
})
