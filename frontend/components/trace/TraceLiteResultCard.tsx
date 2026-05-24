import React from 'react'
import { PublicTraceSummary } from '@/types/trace'
import { TraceBandCard, TraceConfidencePanel, TraceLimitationsPanel, TraceNextStepsPanel, TraceOriginPanel, TracePrivacyPanel, TraceReasonList, TraceSafetyPanel } from './TracePanels'

export function TraceLiteResultCard({ summary }: { summary: PublicTraceSummary }) {
  return <section className='space-y-3 border rounded p-4'><TraceBandCard band={summary.band} /><p><strong>Risk summary:</strong> {summary.risk_summary}</p><TracePrivacyPanel summary={summary} /><TraceOriginPanel summary={summary} /><TraceConfidencePanel summary={summary} /><h3>Top reasons</h3><TraceReasonList reasons={summary.top_reasons || []} /><TraceLimitationsPanel limitations={summary.limitations || []} /><TraceNextStepsPanel /><TraceSafetyPanel /><p className='text-sm text-[var(--muted)]'>Report ID: {summary.report_id}</p></section>
}
