import React from 'react'
import { PublicLayout } from '@/components/layout/PublicLayout'
import { InfrastructureHealthCard, ObservabilitySummary, PlatformReadinessPanel, SystemHealthBanner } from '@/components/operations/PlatformOpsComponents'
export default function Page(){return <PublicLayout><SystemHealthBanner/><InfrastructureHealthCard/><ObservabilitySummary/><PlatformReadinessPanel/></PublicLayout>}
