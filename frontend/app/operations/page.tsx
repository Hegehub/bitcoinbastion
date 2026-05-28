'use client';

import React from 'react'
import { PublicLayout } from '@/components/layout/PublicLayout';
import { SafetyBanner } from '@/components/public/SafetyBanner';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { PAGE_TRANSLATIONS } from '@/lib/i18n';
import { useRuntimeLanguage } from '@/lib/runtimeLanguage';

export default function Page(){const language = useRuntimeLanguage(); const copy = PAGE_TRANSLATIONS[language].operations; return <PublicLayout><h1 className='text-3xl font-bold'>{copy.title}</h1><StatusBadge label='BASELINE'/><p>{copy.summary}</p><SafetyBanner/></PublicLayout>}
