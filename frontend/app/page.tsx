'use client';

import { motion } from 'framer-motion';
import Link from 'next/link';
import { usePublicLanding } from '@/hooks/usePublicLanding';
import { usePublicStatus } from '@/hooks/usePublicStatus';

function Pill({ children }: { children: string }) {
  return <span className='rounded-full border border-bb-border bg-white px-3 py-1 text-xs text-bb-graphite'>{children}</span>;
}

export default function HomePage() {
  const landing = usePublicLanding();
  const status = usePublicStatus();

  const modules = status.data?.modules ?? {};
  const limitations = status.data?.known_limitations ?? ['Public status feed unavailable; showing fallback posture.'];

  return (
    <>
      <section className='bastion-section'>
        <div className='bastion-container'>
          <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }}>
            <p className='bastion-eyebrow'>Bitcoin-native infrastructure you can verify</p>
            <h1 className='mt-4 max-w-4xl text-4xl font-heading leading-tight text-bb-black sm:text-5xl'>
              Operator-controlled, no-custody Bitcoin infrastructure.
            </h1>
            <p className='mt-5 max-w-3xl text-base text-bb-gray sm:text-lg'>
              Evidence over claims. Self-host capable. Built on a Bitcoin-first backend foundation with advisory-only
              workflows and transparent status signals.
            </p>
            <div className='mt-7 flex flex-wrap gap-3'>
              <Link href='/status' className='rounded-xl border border-bb-border bg-white px-4 py-2 font-medium'>
                View Status
              </Link>
              <Link href='/manifesto' className='rounded-xl border border-bb-border bg-white px-4 py-2 font-medium'>
                Read Manifesto
              </Link>
              <Link href='/operations' className='rounded-xl bg-bb-orange px-4 py-2 font-semibold text-white'>
                Self-host
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      <section className='pb-12 sm:pb-16'>
        <div className='bastion-container'>
          <div className='bastion-card'>
            <h2 className='text-xl font-heading'>Live Bastion Status</h2>
            <div className='mt-4 grid gap-3 sm:grid-cols-3'>
              <div className='rounded-xl border p-4'><p className='text-xs text-bb-gray'>Platform status</p><p className='mt-1 font-semibold'>{status.data?.platform_status ?? 'unknown'}</p></div>
              <div className='rounded-xl border p-4'><p className='text-xs text-bb-gray'>Trace status</p><p className='mt-1 font-semibold'>{status.data?.trace_status ?? 'unknown'}</p></div>
              <div className='rounded-xl border p-4'><p className='text-xs text-bb-gray'>Production calibrated</p><p className='mt-1 font-semibold'>{status.data?.production_calibrated ? 'Yes' : 'No'}</p></div>
            </div>
            <div className='mt-4'>
              <p className='text-xs text-bb-gray'>Modules</p>
              <div className='mt-2 flex flex-wrap gap-2'>
                {Object.keys(modules).length
                  ? Object.entries(modules).map(([k, v]) => <Pill key={k}>{`${k}: ${v}`}</Pill>)
                  : <Pill>No module telemetry available</Pill>}
              </div>
            </div>
            <div className='mt-4'>
              <p className='text-xs text-bb-gray'>Known limitations</p>
              <ul className='mt-2 list-disc space-y-1 pl-5 text-sm text-bb-graphite'>
                {limitations.slice(0, 4).map((item) => <li key={item}>{item}</li>)}
              </ul>
            </div>
            {(status.isLoading || landing.isLoading) && <p className='mt-3 text-xs text-bb-gray'>Loading latest public data…</p>}
          </div>
        </div>
      </section>

      <section className='pb-12 sm:pb-16'>
        <div className='bastion-container grid gap-4 md:grid-cols-2 xl:grid-cols-4'>
          <article className='bastion-card'><p className='bastion-eyebrow'>Sovereignty Score</p><h3 className='mt-2 font-heading text-lg'>Preview</h3><p className='mt-2 text-sm text-bb-gray'>Transparent score bands with reason codes and conservative advisory framing.</p></article>
          <article className='bastion-card'><p className='bastion-eyebrow'>Product Constellation</p><h3 className='mt-2 font-heading text-lg'>Preview</h3><p className='mt-2 text-sm text-bb-gray'>Trace, policy, treasury, and platform modules mapped as operator-oriented building blocks.</p></article>
          <article className='bastion-card'><p className='bastion-eyebrow'>Evidence Timeline</p><h3 className='mt-2 font-heading text-lg'>Preview</h3><p className='mt-2 text-sm text-bb-gray'>Time-sequenced evidence snapshots that prioritize auditability over marketing claims.</p></article>
          <article className='bastion-card'><p className='bastion-eyebrow'>Developer Quickstart</p><h3 className='mt-2 font-heading text-lg'>Preview</h3><p className='mt-2 text-sm text-bb-gray'>Public endpoints, typed envelopes, and safe fallbacks for resilient frontend integration.</p></article>
        </div>
      </section>

      <section className='pb-12 sm:pb-16'>
        <div className='bastion-container'>
          <div className='bastion-card'>
            <p className='bastion-eyebrow'>Manifesto</p>
            <h2 className='mt-2 text-2xl font-heading'>No custody. No black boxes. No unverifiable promises.</h2>
            <p className='mt-3 max-w-3xl text-bb-gray'>
              {landing.data?.platform_tagline ?? 'Bitcoin Bastion is advisory-only infrastructure designed for sovereign operators.'}
            </p>
            <div className='mt-5'>
              <Link href='/manifesto' className='rounded-xl bg-bb-orange px-4 py-2 font-semibold text-white'>Read the full manifesto</Link>
            </div>
          </div>
        </div>
      </section>

      <section className='pb-16'>
        <div className='bastion-container'>
          <div className='rounded-2xl border border-bb-border bg-white p-8 text-center'>
            <h2 className='text-2xl font-heading'>Deploy a Bitcoin Bastion you can verify.</h2>
            <p className='mx-auto mt-3 max-w-2xl text-bb-gray'>
              Start with status transparency, evidence-first workflows, and operator-owned infrastructure.
            </p>
            <div className='mt-6 flex flex-wrap justify-center gap-3'>
              <Link href='/status' className='rounded-xl border border-bb-border px-4 py-2 font-medium'>View Status</Link>
              <Link href='/operations' className='rounded-xl bg-bb-orange px-4 py-2 font-semibold text-white'>Self-host Bitcoin Bastion</Link>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
