import React from 'react'
import { PublicLayout } from '@/components/layout/PublicLayout';
import { TraceSummaryCard } from '@/components/trace/TraceSummaryCard';
export default function Report(){const mock={report_id:1,band:'MEDIUM',risk_summary:'Caution',safety_warnings:['Advisory only']};return <PublicLayout><TraceSummaryCard summary={mock}/></PublicLayout>}
