'use client'
import React, { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import { PublicLayout } from '@/components/layout/PublicLayout'
import { apiGet } from '@/services/api'
import { PublicTraceSummary } from '@/types/trace'
import { TraceConfidenceDetails, TraceCounterpartyPanel , TraceEvidenceSummary, TraceLimitationsCard, TraceOperatorGuidance, TraceOriginAnalysis, TracePrivacyAnalysis, TraceReasonBreakdown, TraceReplayInfo, TraceReportHeader, TraceReportSkeleton, TraceStatusBanner, TraceTimeline, TraceUnavailablePanel, TraceOverviewCard } from '@/components/trace/TraceDetailed'

export default function ReportPage() {
  const { reportId } = useParams<{ reportId: string }>()
  const [summary, setSummary] = useState<PublicTraceSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [missing, setMissing] = useState(false)
  useEffect(() => { apiGet<PublicTraceSummary>(`/api/v1/public/trace/${reportId}/summary`).then(setSummary).catch(() => setMissing(true)).finally(() => setLoading(false)) }, [reportId])
  return <PublicLayout><TraceReportHeader id={reportId} /><TraceStatusBanner />{loading ? <TraceReportSkeleton /> : missing || !summary ? <TraceUnavailablePanel /> : <div className='space-y-4'><TraceOverviewCard s={summary} /><TraceTimeline events={summary.top_reasons || []} /><TracePrivacyAnalysis s={summary} /><TraceOriginAnalysis s={summary} /><TraceCounterpartyPanel /><TraceConfidenceDetails s={summary} /><TraceReasonBreakdown reasons={summary.top_reasons || []} /><TraceLimitationsCard s={summary} /><TraceEvidenceSummary /><TraceReplayInfo /><TraceOperatorGuidance /></div>}</PublicLayout>
}
