import React from 'react'
import { PublicLayout } from '@/components/layout/PublicLayout'
import { EnterpriseCapabilityMatrix, EnterpriseDashboard, EnterprisePlaceholderNotice } from '@/components/enterprise/EnterpriseComponents'

export default function Page(){return <PublicLayout><EnterpriseDashboard/><EnterpriseCapabilityMatrix/><EnterprisePlaceholderNotice/></PublicLayout>}
