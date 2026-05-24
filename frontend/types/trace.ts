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
