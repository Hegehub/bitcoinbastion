import React from 'react'
import { PublicLayout } from '@/components/layout/PublicLayout';
import { SafetyBanner } from '@/components/public/SafetyBanner';
import { StatusBadge } from '@/components/ui/StatusBadge';

export default function Page(){return <PublicLayout><h1 className='text-3xl font-bold'>Operations</h1><StatusBadge label='BASELINE'/><p>Kubernetes, GitOps, observability, evidence jobs, backup/restore and recovery drill foundations.</p><SafetyBanner/></PublicLayout>}
