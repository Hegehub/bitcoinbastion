import React from 'react';
import { render, screen } from '@testing-library/react';
import StatusPage from '@/app/status/page';
import { vi } from 'vitest';

vi.mock('@/hooks/useHealth', () => ({ useHealth: () => ({ data: { status: 'unknown', details: { mode: 'fallback' } }, isLoading: false }) }));
vi.mock('@/hooks/usePublicStatus', () => ({ usePublicStatus: () => ({ data: { platform_status: 'unknown', trace_status: 'unknown', production_calibrated: false, modules: {}, known_limitations: [], last_update: 'unknown' }, isLoading: false }) }));
vi.mock('@/hooks/usePublicStats', () => ({ usePublicStats: () => ({ data: { reports_generated: 0, proof_packets_generated: 0, watchtower_entries: 0, runtime_events: 0, supported_modules: [], limitations: [] }, isLoading: false }) }));
vi.mock('@tanstack/react-query', async () => {
  const actual = await vi.importActual<any>('@tanstack/react-query');
  return { ...actual, useQuery: () => ({ data: { status: 'unknown', details: { mode: 'fallback' } }, isLoading: false }) };
});

test('status page shows backend unknown fallback copy', () => {
  render(<StatusPage />);
  expect(screen.getByText(/website online · backend status unknown/i)).toBeTruthy();
});
