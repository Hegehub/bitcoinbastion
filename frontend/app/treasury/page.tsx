import React from 'react'
import { PublicLayout } from '@/components/layout/PublicLayout';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { SafetyBanner } from '@/components/public/SafetyBanner';

export default function Page(){return <PublicLayout><h1 className='text-3xl font-bold'>Treasury</h1><div className='my-2'><StatusBadge label='BASELINE'/><span className='ml-2'><StatusBadge label='NOT PRODUCTION-CALIBRATED'/></span></div><p>This module page is an informational shell for Bitcoin Bastion platform orientation.</p><h2 className='text-xl font-semibold mt-4'>What it does</h2><p>Provides advisory, evidence-oriented workflows for operators.</p><h2 className='text-xl font-semibold mt-4'>What it does not do</h2><p>No custody, no seed/private key handling, no transaction signing/broadcasting.</p><h2 className='text-xl font-semibold mt-4'>Limitations</h2><p>Baseline / placeholder coverage for interactive workflows.</p><SafetyBanner/></PublicLayout>}
