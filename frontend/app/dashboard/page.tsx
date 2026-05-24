import React from 'react'
import { PublicLayout } from '@/components/layout/PublicLayout'
import { DeploymentEvidenceCard, ModuleStatusGrid, ObservabilitySummary, PlatformOverview, PlatformReadinessPanel, PlatformWarningsPanel, RuntimeEventsFeed, SystemHealthBanner } from '@/components/operations/PlatformOpsComponents'

export default function Page(){return <PublicLayout><PlatformOverview/><SystemHealthBanner/><ModuleStatusGrid/><RuntimeEventsFeed/><ObservabilitySummary/><div className='grid md:grid-cols-3 gap-3'><DeploymentEvidenceCard title='Migration status'/><DeploymentEvidenceCard title='Release gates'/><DeploymentEvidenceCard title='Recovery drills'/></div><PlatformReadinessPanel/><PlatformWarningsPanel/></PublicLayout>}
