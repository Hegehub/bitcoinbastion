import React from 'react'
import { PublicLayout } from '@/components/layout/PublicLayout'
import { TraceProofPacketViewer } from '@/components/trace/TraceDetailed'

export default function ProofPacketPage({ params }: { params: { reportId: string } }) {
  return <PublicLayout><TraceProofPacketViewer id={params.reportId} /></PublicLayout>
}
