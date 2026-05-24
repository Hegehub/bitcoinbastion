import { normalizeApiError } from '../services/api'


test('frontend API error normalizer maps stable cases', () => {
  expect(normalizeApiError(new Error('api_error_404'))).toMatch(/not found/i)
  expect(normalizeApiError(new Error('api_error_422'))).toMatch(/invalid/i)
  expect(normalizeApiError(new Error('AbortError'))).toMatch(/timed out/i)
})
