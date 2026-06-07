'use client'
import React, { useEffect, useState } from 'react'
import { PublicLayout } from '@/components/layout/PublicLayout'
import { TraceProofPacketViewer, TraceReportSkeleton } from '@/components/trace/TraceDetailed'
import { apiClient } from '@/services/apiClient'
import { TraceProofPacket } from '@/types/trace'

export default function ProofPacketPage({ params }: { params: { reportId: string } }) {
  const [packet, setPacket] = useState<TraceProofPacket | null>(null)
  const [loading, setLoading] = useState(true)
  const [unavailable, setUnavailable] = useState(false)

  useEffect(() => {
    setLoading(true)
    setUnavailable(false)
    apiClient.getProofPacket(params.reportId)
      .then(setPacket)
      .catch(() => setUnavailable(true))
      .finally(() => setLoading(false))
  }, [params.reportId])

  return <PublicLayout>{loading ? <TraceReportSkeleton /> : <TraceProofPacketViewer id={params.reportId} packet={packet} unavailable={unavailable} />}</PublicLayout>
}
