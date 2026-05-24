import React from 'react'
import { render } from '@testing-library/react'
import RootLayout from '../app/layout'
import { normalizeApiError } from '../services/api'
import CheckPage from '../app/check/page'

test('skip to content link exists', () => {
  const { getByText } = render(<RootLayout><div>body</div></RootLayout>)
  expect(getByText(/Skip to content/i)).toBeTruthy()
})

test('api errors normalized to calm messages', () => {
  expect(normalizeApiError(new Error('api_error_404'))).toMatch(/not found/i)
  expect(normalizeApiError(new Error('api_error_429'))).toMatch(/too many requests/i)
})

test('no forbidden wording and no-custody warning present', () => {
  const { container, getByText } = render(<CheckPage />)
  expect(getByText(/Never enter seed phrases, private keys or wallet files/i)).toBeTruthy()
  const txt = (container.textContent || '').toLowerCase()
  for (const bad of ['clean address', 'dirty address', 'guaranteed safe', 'approved payment', 'criminal address', 'ai verified']) {
    expect(txt.includes(bad)).toBe(false)
  }
})
