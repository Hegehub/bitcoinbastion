'use client';

import { usePublicStats } from '@/hooks/usePublicStats';

type EvidenceItem = { id: string; title: string; category: string; mode: 'demo' | 'baseline'; note: string; timestamp: string };

const DEMO_EVIDENCE: EvidenceItem[] = [
  { id: 'ev-001', title: 'Runtime status snapshot', category: 'Runtime Evidence', mode: 'baseline', note: 'Public status telemetry sample.', timestamp: '2026-05-20T10:00:00Z' },
  { id: 'ev-002', title: 'Provider health corroboration', category: 'Provider Evidence', mode: 'demo', note: 'Demo-only provider signal sample.', timestamp: '2026-05-19T18:30:00Z' },
  { id: 'ev-003', title: 'Deployment evidence pack pointer', category: 'Deployment Evidence', mode: 'baseline', note: 'Baseline deployment artifact reference.', timestamp: '2026-05-18T14:10:00Z' },
  { id: 'ev-004', title: 'Security control checklist run', category: 'Security Evidence', mode: 'demo', note: 'Demo checklist output. Not a production attestation.', timestamp: '2026-05-17T11:42:00Z' },
  { id: 'ev-005', title: 'No-custody policy assertion', category: 'No-Custody Evidence', mode: 'baseline', note: 'Policy boundary statement.', timestamp: '2026-05-16T09:12:00Z' },
  { id: 'ev-006', title: 'Release gate checklist sample', category: 'Release Evidence', mode: 'demo', note: 'Synthetic release evidence sample.', timestamp: '2026-05-15T21:20:00Z' },
];

const CATEGORIES = ['Runtime Evidence', 'Provider Evidence', 'Deployment Evidence', 'Security Evidence', 'No-Custody Evidence', 'Release Evidence'];

export function EvidenceDashboard() {
  const stats = usePublicStats();

  return (
    <div className='space-y-6'>
      <section className='rounded-xl border border-bb-warning bg-bb-orange-soft p-4 text-sm'>
        <strong>Baseline/demo notice:</strong> This page may include demo or baseline evidence cards when production-calibrated evidence streams are unavailable. Demo entries are explicitly labeled and are not production attestations.
      </section>

      <section className='grid gap-4 lg:grid-cols-2'>
        <article className='bastion-card'>
          <h2 className='text-xl font-heading'>Proof Packet Viewer</h2>
          <p className='mt-2 text-sm text-bb-gray'>Public proof packet counts and advisory context.</p>
          <p className='mt-4 text-3xl font-heading'>{stats.data?.proof_packets_generated ?? 0}</p>
          <p className='text-xs text-bb-gray'>Proof packets generated (public stats feed)</p>
        </article>
        <article className='bastion-card'>
          <h2 className='text-xl font-heading'>Public Trust Ledger</h2>
          <p className='mt-2 text-sm text-bb-gray'>Traceable public-safe record summaries.</p>
          <ul className='mt-3 space-y-1 text-sm'>
            <li>Reports generated: {stats.data?.reports_generated ?? 0}</li>
            <li>Runtime events: {stats.data?.runtime_events ?? 0}</li>
            <li>Watchtower entries: {stats.data?.watchtower_entries ?? 0}</li>
          </ul>
        </article>
      </section>

      <section className='bastion-card'>
        <h2 className='text-xl font-heading'>Evidence categories</h2>
        <div className='mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-3'>
          {CATEGORIES.map((c) => <div key={c} className='rounded-lg border p-3 text-sm font-medium'>{c}</div>)}
        </div>
      </section>

      <section className='bastion-card'>
        <h2 className='text-xl font-heading'>Evidence Timeline</h2>
        <ul className='mt-4 space-y-3'>
          {DEMO_EVIDENCE.map((e) => (
            <li key={e.id} className='rounded-lg border p-4'>
              <div className='flex flex-wrap items-center gap-2'>
                <p className='font-semibold'>{e.title}</p>
                <span className={`rounded-full px-2 py-0.5 text-xs ${e.mode === 'demo' ? 'bg-bb-warning/20 text-bb-warning' : 'bg-bb-bg-soft text-bb-graphite'}`}>
                  {e.mode.toUpperCase()}
                </span>
              </div>
              <p className='mt-1 text-xs text-bb-gray'>{e.category} · {new Date(e.timestamp).toISOString()}</p>
              <p className='mt-2 text-sm text-bb-gray'>{e.note}</p>
            </li>
          ))}
        </ul>
      </section>

      <section className='bastion-card'>
        <h2 className='text-xl font-heading'>Evidence model and limitations</h2>
        <ul className='mt-3 list-disc space-y-2 pl-5 text-sm text-bb-graphite'>
          <li><strong>Evidence over claims:</strong> assertions should map to verifiable artifacts.</li>
          <li><strong>Baseline vs production calibrated:</strong> baseline signals indicate initial posture, not full production attestation.</li>
          <li><strong>Synthetic vs real evidence:</strong> demo/synthetic items are explicitly labeled and must not be treated as production truth.</li>
          <li><strong>Advisory-only limitations:</strong> outputs support operator judgment and do not execute custody or signing actions.</li>
        </ul>
      </section>
    </div>
  );
}
