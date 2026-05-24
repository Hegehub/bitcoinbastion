import React from 'react'
import { PublicLayout } from '@/components/layout/PublicLayout'
import { BusinessPolicyEditor, BusinessPolicyProfileCard } from '@/components/business/BusinessComponents'

export default function Page(){return <PublicLayout><BusinessPolicyProfileCard/><BusinessPolicyEditor/></PublicLayout>}
