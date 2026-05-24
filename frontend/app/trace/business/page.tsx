import React from 'react'
import { PublicLayout } from '@/components/layout/PublicLayout'
import { BatchResultTable, BusinessDashboard, BusinessPolicyProfileCard, BusinessProofPacketActions, ReviewDeskTable } from '@/components/business/BusinessComponents'

export default function Page(){return <PublicLayout><BusinessDashboard/><BatchResultTable/><ReviewDeskTable/><BusinessPolicyProfileCard/><BusinessProofPacketActions/></PublicLayout>}
