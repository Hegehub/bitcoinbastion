'use client';

import React from 'react'
import { PublicLayout } from '@/components/layout/PublicLayout';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { SafetyBanner } from '@/components/public/SafetyBanner';
import { PAGE_TRANSLATIONS } from '@/lib/i18n';
import { useRuntimeLanguage } from '@/lib/runtimeLanguage';

export default function Page(){const language = useRuntimeLanguage(); const copy = PAGE_TRANSLATIONS[language].platform; return <PublicLayout><h1 className='text-3xl font-bold'>{copy.title}</h1><div className='my-2'><StatusBadge label='BASELINE'/><span className='ml-2'><StatusBadge label='NOT PRODUCTION-CALIBRATED'/></span></div><p>{copy.summary}</p><h2 className='text-xl font-semibold mt-4'>What it does</h2><p>Provides advisory, evidence-oriented workflows for operators.</p><h2 className='text-xl font-semibold mt-4'>What it does not do</h2><p>No custody, no seed/private key handling, no transaction signing/broadcasting.</p><h2 className='text-xl font-semibold mt-4'>Limitations</h2><p>Baseline / placeholder coverage for interactive workflows.</p><SafetyBanner/></PublicLayout>}
