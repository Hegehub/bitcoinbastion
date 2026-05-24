import React from 'react'
import { PublicLayout } from '@/components/layout/PublicLayout';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { SafetyBanner } from '@/components/public/SafetyBanner';

export default function Page(){return <PublicLayout><h1 className='text-3xl font-bold'>Register</h1><div className='my-2'><StatusBadge label='BASELINE'/></div><p>Bitcoin Bastion Register shell for merchant payment advisory and future offline/local-node workflows.</p><p>Register integration does not auto-accept or auto-reject payments.</p><SafetyBanner/></PublicLayout>}
