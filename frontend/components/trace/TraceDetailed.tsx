import React from 'react'
import { PublicTraceSummary, TraceProofPacket } from '@/types/trace'

export const TraceReportHeader = ({ id }: { id: string }) => <header><h1 className='text-2xl font-bold'>Trace Report #{id}</h1><p className='text-sm'>Advisory-only evidence summary.</p></header>
export const TraceStatusBanner = () => <div className='border rounded p-3 text-sm'><p>Bastion Trace provides heuristic evidence-based analysis and does not provide legal verification or Bitcoin consensus proof.</p><p>No custody. Public Bitcoin addresses only. Never enter seed phrases, private keys, wallet files or signing material.</p></div>
export const TraceOverviewCard = ({ s }: { s: PublicTraceSummary }) => <section className='border rounded p-4'><p><b>Band:</b> {s.band}</p><p><b>Risk:</b> {s.risk_summary}</p><p><b>Privacy:</b> {s.privacy_summary}</p><p><b>Origin:</b> {s.origin_summary}</p><p><b>Confidence:</b> {s.confidence_summary}</p><p><b>Manual review:</b> {s.manual_review_recommended ? 'Recommended' : 'Not currently indicated'}</p></section>
export const TraceTimelineEvent = ({ e }: { e: string }) => <li className='border-l-2 pl-3 py-1'>Signal observed: {e}</li>
export const TraceTimeline = ({ events }: { events: string[] }) => <section><h2>Timeline</h2><ul>{events.map((e) => <TraceTimelineEvent key={e} e={e} />)}</ul></section>
export const TraceReasonBreakdown = ({ reasons }: { reasons: string[] }) => <section><h2>Reasons</h2><ul>{reasons.map((r) => <li key={r}>{r.replaceAll('_', ' ').toLowerCase()}</li>)}</ul></section>
export const TraceEvidenceSummary = () => <section><h2>Evidence Summary</h2><p>Evidence references are summarized in public-safe form.</p></section>
export const TraceOriginAnalysis = ({ s }: { s: PublicTraceSummary }) => <section><h2>Origin</h2><p>{s.origin_summary || 'Insufficient information for strong attribution.'}</p></section>
export const TracePrivacyAnalysis = ({ s }: { s: PublicTraceSummary }) => <section><h2>Privacy</h2><p>{s.privacy_summary}. Privacy analysis is probabilistic and source-limited.</p></section>
export const TraceCounterpartyPanel = () => <section><h2>Counterparty</h2><p>Counterparty exposure indicators are advisory only; manual review triggers may apply.</p></section>
export const TraceConfidenceDetails = ({ s }: { s: PublicTraceSummary }) => <section><h2>Confidence</h2><p>{s.confidence_summary}. Low confidence may indicate limited evidence or provider disagreement.</p></section>
export const TraceLimitationsCard = ({ s }: { s: PublicTraceSummary }) => <section><h2>Limitations</h2><ul>{(s.limitations || []).map((l) => <li key={l}>{l}</li>)}<li>Not legal verification</li><li>Not Bitcoin consensus proof</li></ul></section>
export const TraceReplayInfo = () => <section><h2>Replay</h2><p>Replay evidence snapshot unavailable.</p></section>
export const TraceOperatorGuidance = () => <section><h2>Operator Guidance</h2><ul><li>Perform additional review for large-value transfers.</li><li>Verify counterparties independently.</li><li>Use additional evidence sources where appropriate.</li></ul></section>
export const TraceReportSkeleton = () => <div className='animate-pulse border rounded p-4'>Loading report…</div>
export const TraceUnavailablePanel = () => <div className='border rounded p-4'>Report unavailable or not found.</div>

export function TraceProofPacketViewer({ id, packet, unavailable }: { id: string; packet?: TraceProofPacket | null; unavailable?: boolean }) {
  return <section className='space-y-3'><h1 className='text-2xl font-bold'>Proof Packet #{id}</h1><ul><li>Advisory-only</li><li>No custody</li><li>Not legal verification</li><li>Not Bitcoin consensus proof</li></ul>{unavailable ? <p>Proof packet unavailable or not found.</p> : null}{packet ? <div className='space-y-3'><p>{packet.signed ? 'Signed evidence summary.' : 'Unsigned application-level evidence summary.'}</p><p>Signature available: {packet.signature_available ? 'yes' : 'no'}</p><h2>Evidence References</h2>{packet.evidence_refs.length ? <ul>{packet.evidence_refs.map((ref, index) => <li key={ref.evidence_ref || index}>{ref.evidence_ref || ref.description || `Evidence ${index + 1}`}</li>)}</ul> : <p>No evidence references are available for this packet.</p>}<h2>Limitations</h2><ul>{packet.limitations.map((limitation) => <li key={limitation}>{limitation}</li>)}</ul></div> : null}<p>Proof packets are evidence bundles and not legal certificates.</p></section>
}
