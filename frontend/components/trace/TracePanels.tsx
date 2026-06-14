import React from 'react'
import { PublicTraceSummary } from '@/types/trace'

export const TraceBandCard = ({ band }: { band: string }) => <div className='border-l-4 border-orange-500 p-3'><strong>Risk band:</strong> {band}</div>
export const TraceReasonList = ({ reasons }: { reasons: string[] }) => <ul>{reasons.map((r) => <li key={r}>• {r}</li>)}</ul>
export const TraceLimitationsPanel = ({ limitations }: { limitations: string[] }) => <div><h3>Limitations</h3><TraceReasonList reasons={limitations.length ? limitations : ['Advisory-only baseline output.']} /></div>
export const TraceSafetyPanel = () => <div><h3>Safety Warnings</h3><ul><li>Never enter seed phrases, private keys, wallet files or signing material.</li><li>Analysis is advisory-only.</li><li>Results are not legal verification or Bitcoin consensus proof.</li></ul></div>
export const TraceConfidencePanel = ({ summary }: { summary: PublicTraceSummary }) => <div><h3>Confidence</h3><p>{summary.confidence_summary}. Low confidence may indicate limited available evidence or provider disagreement.</p></div>
export const TracePrivacyPanel = ({ summary }: { summary: PublicTraceSummary }) => <div><h3>Privacy</h3><p>{summary.privacy_summary}. Privacy exposure does not imply illicit certainty.</p></div>
export const TraceOriginPanel = ({ summary }: { summary: PublicTraceSummary }) => <div><h3>Origin</h3><p>{summary.origin_summary || 'Insufficient information for strong origin attribution.'}</p></div>
export const TraceNextStepsPanel = () => <div><h3>Suggested Next Steps</h3><ul><li>Perform manual review for large-value transfers.</li><li>Use additional evidence sources where appropriate.</li><li>Verify counterparties independently.</li></ul></div>
