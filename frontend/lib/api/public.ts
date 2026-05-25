import { fetchEnvelope } from '@/lib/api/client';
import type {
  PublicFeatureEntry,
  PublicLandingResponse,
  PublicRoadmapResponse,
  PublicStatsResponse,
  PublicStatusResponse,
} from '@/types/public-api';

const publicFallback = {
  landing: {
    platform_name: 'Bitcoin Bastion',
    platform_tagline: 'Security-first advisory intelligence for Bitcoin operators.',
    modules: ['Trace', 'Policy', 'Citadel'],
    status_summary: { mode: 'fallback' },
    feature_catalog: [],
    roadmap_summary: { mode: 'fallback' },
    safety_principles: ['Advisory only', 'No custody'],
    production_readiness: { mode: 'fallback' },
    links: {},
  } satisfies PublicLandingResponse,
  status: {
    platform_status: 'unknown',
    trace_status: 'unknown',
    production_calibrated: false,
    modules: {},
    known_limitations: ['Live backend unavailable during static build.'],
    last_update: new Date(0).toISOString(),
  } satisfies PublicStatusResponse,
  roadmap: {
    current_phase: 'baseline',
    implemented: [],
    baseline: [],
    placeholder: [],
    planned: [],
    not_started: [],
  } satisfies PublicRoadmapResponse,
  stats: {
    reports_generated: 0,
    proof_packets_generated: 0,
    watchtower_entries: 0,
    runtime_events: 0,
    supported_modules: [],
    limitations: ['Live backend unavailable during static build.'],
  } satisfies PublicStatsResponse,
  features: [] as PublicFeatureEntry[],
};

export const publicApi = {
  getLanding: () => fetchEnvelope<PublicLandingResponse>('/api/v1/public/landing', publicFallback.landing),
  getStatus: () => fetchEnvelope<PublicStatusResponse>('/api/v1/public/status', publicFallback.status),
  getRoadmap: () => fetchEnvelope<PublicRoadmapResponse>('/api/v1/public/roadmap', publicFallback.roadmap),
  getStats: () => fetchEnvelope<PublicStatsResponse>('/api/v1/public/stats', publicFallback.stats),
  getFeatures: () => fetchEnvelope<PublicFeatureEntry[]>('/api/v1/public/features', publicFallback.features),
};
