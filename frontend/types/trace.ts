export type LiteTraceResult = {
  address: string
  chain: string
  status_label: string
  risk_label: string
  privacy_label: string
  origin_label: string
  confidence_label: string
  safe_to_send_advisory: string
  short_summary: string
  what_this_means: string
  recommended_next_step: string
  warnings: string[]
  limitations: string[]
  report_id: number
  created_at?: string
}

export type PublicTraceSummary = {
  report_id: number
  band: string
  risk_summary: string
  privacy_summary: string
  origin_summary: string
  confidence_summary: string
  manual_review_recommended: boolean
  top_reasons: string[]
  limitations: string[]
  safety_warnings: string[]
  created_at?: string
}

export type TraceReport = {
  id: number
  address: string
  chain: string
  trace_score: number
  trace_band: string
  confidence: number
  source_quality: string
  freshness: string
  reason_codes: string[]
  evidence_refs: string[]
  limitations: string[]
  operator_guidance: string[]
  advisory_not_legal_verdict: boolean
  not_consensus_proof: boolean
  no_custody: boolean
  created_at?: string
}

export type TraceEvidence = {
  id: number
  report_id: number
  evidence_type: string
  source_name: string
  source_type: string
  confidence: number
  freshness_days?: number | null
  description: string
  limitations: string[]
  evidence_ref: string
  created_at?: string
}

export type TraceProofPacketEvidenceRef = {
  id?: number
  evidence_ref?: string
  evidence_type?: string
  source_name?: string
  source_type?: string
  confidence?: number
  freshness_days?: number | null
  description?: string
  limitations?: string[]
  created_at?: string | null
}

export type TraceProofPacket = {
  report_id: number
  address?: string
  trace_band?: string
  trace_score?: number
  confidence?: number
  advisory_only: boolean
  not_legal_verification: boolean
  not_bitcoin_consensus_proof: boolean
  no_custody: boolean
  signed: boolean
  signature_available: boolean
  signature_status: string
  packet_type: string
  evidence_refs: TraceProofPacketEvidenceRef[]
  report_evidence_refs?: string[]
  limitations: string[]
  operator_guidance?: string[]
  created_at?: string | null
}

export type TraceStatus = {
  status: string
  trace_available: boolean
  calibration_status: string
  provider_status: string
  limitations: string[]
  trace_production_calibrated?: boolean
}

export type TraceRuntimeEvent = {
  id?: number
  event_type: string
  severity: string
  operation?: string
  status?: string
  message?: string
  metadata_json?: Record<string, unknown>
  created_at?: string
}
