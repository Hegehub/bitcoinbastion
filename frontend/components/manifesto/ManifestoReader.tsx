'use client';

import Link from 'next/link';
import { useMemo, useState } from 'react';

type ReaderMode = 'simple' | 'technical' | 'operator';

type Principle = {
  slug: string;
  title: string;
  statement: string;
  explanation: string;
  consequence: string;
  technical?: string;
  operator?: string;
};

const PRINCIPLES: Principle[] = [
  {
    slug: 'bitcoin-first',
    title: 'Bitcoin first',
    statement: 'Bitcoin is the base layer, not an optional integration.',
    explanation: 'System decisions prioritize Bitcoin-native constraints, data models, and operational realities.',
    consequence: 'Roadmaps and risk models are evaluated against Bitcoin-specific failure modes first.',
    technical: 'Schemas, scoring, and telemetry contracts are designed around Bitcoin primitives and deterministic interfaces.',
    operator: 'Runbooks assume Bitcoin-node, mempool, and chain-state visibility as baseline inputs.',
  },
  {
    slug: 'no-custody',
    title: 'No custody',
    statement: 'Bitcoin Bastion never takes possession of user funds.',
    explanation: 'The platform is advisory and operational, not a wallet or custodian.',
    consequence: 'Features must avoid private-key handling, signing, or transaction custody workflows.',
    technical: 'Public address intelligence and policy orchestration are separated from signing surfaces.',
    operator: 'Teams keep key material in dedicated custody hardware and isolate Bastion from signing authority.',
  },
  {
    slug: 'evidence-over-claims',
    title: 'Evidence over claims',
    statement: 'Assertions require verifiable evidence artifacts.',
    explanation: 'Confidence must be attached to explainable provenance, not opaque score outputs.',
    consequence: 'Every major decision surface includes rationale, limitations, and confidence notes.',
    technical: 'Trace and policy modules emit reason codes, source references, and reproducible metadata snapshots.',
    operator: 'Analysts treat unsupported claims as unresolved until corroborated by independent evidence.',
  },
  {
    slug: 'self-hosted-by-design',
    title: 'Self-hosted by design',
    statement: 'Sovereign operation is a first-class deployment mode.',
    explanation: 'Users can run the platform on infrastructure they control.',
    consequence: 'Deployment architecture avoids lock-in to single managed vendors.',
    technical: 'Containerized services, documented environment variables, and explicit runtime dependencies are required.',
    operator: 'Ops teams can deploy, monitor, and recover with their own controls and credentials.',
  },
  {
    slug: 'no-black-box-trust',
    title: 'No black-box trust',
    statement: 'Critical outcomes cannot depend on hidden logic.',
    explanation: 'High-impact decisions require transparent pathways from signal to conclusion.',
    consequence: 'Opaque model outputs must be bounded and paired with human-readable context.',
    technical: 'APIs expose data lineage and constraints alongside computed summaries.',
    operator: 'Risk review workflows require explainability before escalation or execution.',
  },
  {
    slug: 'operator-control',
    title: 'Operator control',
    statement: 'Operators own final authority over actions and policy.',
    explanation: 'Automation supports operators; it does not replace governance responsibility.',
    consequence: 'Policy, alerting, and release gates remain operator-configurable and auditable.',
    technical: 'Role boundaries and explicit approvals are encoded in workflows.',
    operator: 'Teams can halt, override, or degrade workflows under documented incident procedures.',
  },
  {
    slug: 'human-confirmation',
    title: 'Human confirmation for risky actions',
    statement: 'High-risk actions require explicit human confirmation.',
    explanation: 'No autonomous path should execute sensitive outcomes without review.',
    consequence: 'Risk thresholds trigger mandatory review and acknowledgment steps.',
    technical: 'Workflow states include pending-review gates and immutable audit timestamps.',
    operator: 'Approvers validate context, evidence, and policy before proceeding.',
  },
  {
    slug: 'privacy-by-default',
    title: 'Privacy by default',
    statement: 'Privacy-preserving behavior is the baseline posture.',
    explanation: 'Data access and display patterns minimize unnecessary exposure.',
    consequence: 'Interfaces default to least disclosure while preserving useful operations.',
    technical: 'Public-safe schemas and redaction boundaries are enforced at API and presentation layers.',
    operator: 'Teams review data-sharing and retention settings as part of release readiness.',
  },
  {
    slug: 'ai-never-controls-keys',
    title: 'AI must never control seed phrases or private keys',
    statement: 'AI systems must have zero authority over secret key material.',
    explanation: 'No model or automation path may handle mnemonic seeds or signing keys.',
    consequence: 'Any workflow requiring key access is outside the platform boundary.',
    technical: 'Input validation and UI guardrails reject sensitive wallet material on public surfaces.',
    operator: 'Security policies treat key-handling attempts as critical incidents.',
  },
  {
    slug: 'sovereignty-system-property',
    title: 'Sovereignty is a system property',
    statement: 'Sovereignty is engineered across architecture, process, and operations.',
    explanation: 'It is not a slogan; it emerges from controllable, recoverable system design.',
    consequence: 'Dependency choices are judged by failure isolation and recoverability.',
    technical: 'Configuration, observability, and recovery drills are part of platform definition.',
    operator: 'Operational ownership includes backups, restore tests, and incident playbooks.',
  },
  {
    slug: 'visible-degraded-states',
    title: 'Fallback and degraded states must be visible',
    statement: 'Users must always see when the system is degraded or in fallback mode.',
    explanation: 'Hidden degradation erodes trust and invites operational mistakes.',
    consequence: 'Status, limitations, and degraded modes are surfaced clearly in UI and API outputs.',
    technical: 'Health/status contracts include explicit degraded indicators and known-limitation fields.',
    operator: 'Operators communicate service posture before advising downstream decisions.',
  },
  {
    slug: 'readiness-proven',
    title: 'Production readiness must be proven, not claimed',
    statement: 'Readiness requires evidence, gates, and repeatable validation.',
    explanation: 'Marketing statements are not substitutes for test outcomes and operational proof.',
    consequence: 'Releases require objective checks for security, reliability, and recoverability.',
    technical: 'CI/CD gates, deployment evidence, and runbook validation are release prerequisites.',
    operator: 'Teams publish readiness evidence and rollback criteria before go-live decisions.',
  },
];

export function ManifestoReader() {
  const [mode, setMode] = useState<ReaderMode>('simple');

  const modeLabel = useMemo(() => {
    if (mode === 'technical') return 'Technical';
    if (mode === 'operator') return 'Operator';
    return 'Simple';
  }, [mode]);

  return (
    <div className='bastion-section'>
      <div className='bastion-container'>
        <header className='mx-auto max-w-4xl'>
          <p className='bastion-eyebrow'>Editorial</p>
          <h1 className='mt-3 text-4xl font-heading leading-tight sm:text-5xl'>Bitcoin Bastion Manifesto</h1>
          <p className='mt-4 text-bb-gray'>
            A production-minded set of principles for Bitcoin-native infrastructure: serious, verifiable, and operator-led.
          </p>
        </header>

        <div className='mt-8 flex flex-wrap items-center gap-3'>
          {(['simple', 'technical', 'operator'] as const).map((entry) => (
            <button
              key={entry}
              type='button'
              onClick={() => setMode(entry)}
              aria-pressed={mode === entry}
              className={`rounded-full border px-4 py-2 text-sm ${
                mode === entry ? 'border-bb-orange bg-bb-orange-soft text-bb-black' : 'border-bb-border bg-white text-bb-graphite'
              }`}
            >
              {entry[0].toUpperCase() + entry.slice(1)}
            </button>
          ))}
          <span className='text-xs text-bb-gray'>Reader mode: {modeLabel}</span>
        </div>

        <nav aria-label='Manifesto anchors' className='mt-6 rounded-2xl border bg-white p-4'>
          <p className='text-xs font-semibold uppercase tracking-wider text-bb-gray'>Jump to principle</p>
          <ol className='mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-3'>
            {PRINCIPLES.map((p, i) => (
              <li key={p.slug}>
                <a href={`#${p.slug}`} className='text-sm text-bb-graphite hover:text-bb-orange'>
                  {i + 1}. {p.title}
                </a>
              </li>
            ))}
          </ol>
        </nav>

        <div className='mt-8 space-y-5'>
          {PRINCIPLES.map((p, i) => (
            <article key={p.slug} id={p.slug} className='bastion-card scroll-mt-24'>
              <p className='text-xs font-semibold uppercase tracking-wider text-bb-orange'>Principle {i + 1}</p>
              <h2 className='mt-2 text-2xl font-heading'>{p.title}</h2>
              <p className='mt-3 text-base font-medium text-bb-black'>{p.statement}</p>
              <p className='mt-3 text-bb-gray'>{p.explanation}</p>
              <div className='mt-4 rounded-xl border border-bb-border bg-bb-bg-soft p-4'>
                <h3 className='font-heading text-sm uppercase tracking-wide text-bb-graphite'>Operational consequence</h3>
                <p className='mt-2 text-sm text-bb-graphite'>{p.consequence}</p>
              </div>
              {mode === 'technical' && p.technical ? (
                <p className='mt-4 text-sm text-bb-graphite'><strong>Technical:</strong> {p.technical}</p>
              ) : null}
              {mode === 'operator' && p.operator ? (
                <p className='mt-4 text-sm text-bb-graphite'><strong>Operator:</strong> {p.operator}</p>
              ) : null}
              <div className='mt-4'>
                <a href={`#${p.slug}`} className='text-xs text-bb-gray underline hover:text-bb-orange'>
                  Shareable link: #{p.slug}
                </a>
              </div>
            </article>
          ))}
        </div>

        <section className='mt-10 rounded-2xl border border-bb-border bg-white p-6 sm:p-8'>
          <h2 className='text-2xl font-heading'>Operate with proof, not promises.</h2>
          <p className='mt-3 text-bb-gray'>
            Explore hardening and sovereignty operations or review the security posture before deployment.
          </p>
          <div className='mt-5 flex flex-wrap gap-3'>
            <Link href='/self-host' className='rounded-xl bg-bb-orange px-4 py-2 font-semibold text-white'>
              Self-host Bitcoin Bastion
            </Link>
            <Link href='/security' className='rounded-xl border border-bb-border px-4 py-2 font-medium'>
              Review Security
            </Link>
          </div>
        </section>
      </div>
    </div>
  );
}
