import React from 'react';
import { render, screen } from '@testing-library/react';
import HomePage from '@/app/page';
import { vi } from 'vitest';

vi.mock('@/hooks/usePublicLanding', () => ({ usePublicLanding: () => ({ data: { platform_tagline: 'tagline' }, isLoading: false }) }));
vi.mock('@/hooks/usePublicStatus', () => ({ usePublicStatus: () => ({ data: { modules: {}, known_limitations: [], production_calibrated: false, platform_status: 'unknown', trace_status: 'unknown' }, isLoading: false }) }));

test('homepage renders hero headline', () => {
  render(<HomePage />);
  expect(screen.getByRole('heading', { name: /operator-controlled, no-custody bitcoin infrastructure/i })).toBeTruthy();
});
