import React from 'react'
import { PublicLayout } from '@/components/layout/PublicLayout'
import { AuditHashChainStatus, AuditLogViewer } from '@/components/enterprise/EnterpriseComponents'

export default function Page(){return <PublicLayout><AuditLogViewer/><AuditHashChainStatus/></PublicLayout>}
