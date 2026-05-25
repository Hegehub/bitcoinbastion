import { ApiClientError, fetchEnvelope, fetchJson } from '@/lib/api/client';
import { vi } from 'vitest';

test('fetchJson returns fallback when base url missing', async () => {
  const res = await fetchJson('/x', undefined, { ok: true });
  expect(res).toEqual({ ok: true });
});

test('fetchEnvelope returns envelope data', async () => {
  vi.stubGlobal('fetch', vi.fn(async () => ({ ok: true, json: async () => ({ success: true, data: { a: 1 } }) })) as any);
  process.env.NEXT_PUBLIC_API_BASE_URL = 'http://localhost:8000';
  const out = await fetchEnvelope<{ a: number }>('/api/v1/public/status');
  expect(out.a).toBe(1);
});

test('fetchJson throws typed error for bad status without fallback', async () => {
  vi.stubGlobal('fetch', vi.fn(async () => ({ ok: false, status: 404, json: async () => ({}) })) as any);
  process.env.NEXT_PUBLIC_API_BASE_URL = 'http://localhost:8000';
  await expect(fetchJson('/bad')).rejects.toBeInstanceOf(ApiClientError);
});
