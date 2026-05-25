export type PublicFeatureStatus =
  | 'IMPLEMENTED'
  | 'BASELINE'
  | 'PLACEHOLDER'
  | 'PLANNED'
  | 'NOT_IMPLEMENTED';

export type PublicFeatureAvailability = 'PUBLIC' | 'PRO' | 'BUSINESS' | 'ENTERPRISE' | 'INTERNAL';

export interface PublicFeatureEntry {
  id: string;
  name: string;
  category: string;
  summary: string;
  status: PublicFeatureStatus;
  availability: PublicFeatureAvailability;
  safety_notes: string[];
  limitations: string[];
}

export interface PublicTraceSummary {
  report_id: number;
  band: string;
  risk_summary: string;
  privacy_summary: string;
  origin_summary: string;
  confidence_summary: string;
  manual_review_recommended: boolean;
  top_reasons: string[];
  limitations: string[];
  safety_warnings: string[];
  created_at: string | null;
}

export interface PublicStatusResponse {
  platform_status: string;
  trace_status: string;
  production_calibrated: boolean;
  modules: Record<string, string>;
  known_limitations: string[];
  last_update: string;
}

export interface PublicRoadmapResponse {
  current_phase: string;
  implemented: string[];
  baseline: string[];
  placeholder: string[];
  planned: string[];
  not_started: string[];
}

export interface PublicStatsResponse {
  reports_generated: number;
  proof_packets_generated: number;
  watchtower_entries: number;
  runtime_events: number;
  supported_modules: string[];
  limitations: string[];
}

export interface PublicLandingResponse {
  platform_name: string;
  platform_tagline: string;
  modules: string[];
  status_summary: Record<string, unknown>;
  feature_catalog: PublicFeatureEntry[];
  roadmap_summary: Record<string, unknown>;
  safety_principles: string[];
  production_readiness: Record<string, unknown>;
  links: Record<string, string>;
}

export interface ResponseEnvelope<T> {
  success: boolean;
  data: T;
}

export interface HealthResponse {
  status: string;
  app: string;
  details: Record<string, string>;
}
