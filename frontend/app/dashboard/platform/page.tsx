import React from 'react'
import { PublicLayout } from '@/components/layout/PublicLayout'
import { ModuleStatusGrid, PlatformOverview, PlatformWarningsPanel } from '@/components/operations/PlatformOpsComponents'
export default function Page(){return <PublicLayout><PlatformOverview/><ModuleStatusGrid/><PlatformWarningsPanel/></PublicLayout>}
