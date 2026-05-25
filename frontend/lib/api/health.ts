import { fetchJson } from '@/lib/api/client';
import type { HealthResponse } from '@/types/public-api';

const healthFallback: HealthResponse = {
  status: 'unknown',
  app: 'bitcoin-bastion',
  details: { mode: 'fallback' },
};

export const healthApi = {
  getHealth: () => fetchJson<HealthResponse>('/api/v1/health', undefined, healthFallback),
  getLive: () => fetchJson<HealthResponse>('/api/v1/health/live', undefined, healthFallback),
  getReady: () => fetchJson<HealthResponse>('/api/v1/health/ready', undefined, healthFallback),
};
