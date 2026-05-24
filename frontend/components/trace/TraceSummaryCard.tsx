import React from 'react'
import { PublicTraceSummary } from '@/types/public';
export function TraceSummaryCard({summary}:{summary:PublicTraceSummary}){return <section aria-label='Trace summary'><h2 className='text-xl font-semibold'>Trace Summary</h2><p>{summary.risk_summary}</p><p>Band: {summary.band}</p></section>}
