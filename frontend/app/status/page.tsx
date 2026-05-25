'use client';

import { useMemo } from 'react';
import { useHealth } from '@/hooks/useHealth';
import { usePublicStats } from '@/hooks/usePublicStats';
import { usePublicStatus } from '@/hooks/usePublicStatus';
import { healthApi } from '@/lib/api/health';
import { useQuery } from '@tanstack/react-query';

function StatusPill({ label, tone }: { label: string; tone: 'good' | 'warn' | 'unknown' }) {
  const toneClass = tone === 'good' ? 'bg-bb-success/15 text-bb-success border-bb-success/30' : tone === 'warn' ? 'bg-bb-warning/15 text-bb-warning border-bb-warning/30' : 'bg-bb-bg-soft text-bb-graphite border-bb-border';
  return <span className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold ${toneClass}`}>{label}</span>;
}

export default function StatusPage() {
  const health = useHealth();
  const live = useQuery({ queryKey: ['health', 'live'], queryFn: healthApi.getLive, staleTime: 10_000 });
  const ready = useQuery({ queryKey: ['health', 'ready'], queryFn: healthApi.getReady, staleTime: 10_000 });
  const publicStatus = usePublicStatus();
  const publicStats = usePublicStats();

  const loading = health.isLoading || live.isLoading || ready.isLoading || publicStatus.isLoading || publicStats.isLoading;

  const isFallback = useMemo(() => {
    return (
      health.data?.details?.mode === 'fallback' ||
      live.data?.details?.mode === 'fallback' ||
      ready.data?.details?.mode === 'fallback' ||
      publicStatus.data?.platform_status === 'unknown'
    );
  }, [health.data, live.data, ready.data, publicStatus.data]);

  const orbTone: 'good' | 'warn' | 'unknown' = isFallback
    ? 'unknown'
    : publicStatus.data?.production_calibrated
      ? 'good'
      : 'warn';

  return (
    <div className='bastion-section'>
      <div className='bastion-container space-y-6'>
        <header>
          <p className='bastion-eyebrow'>Live Status</p>
          <h1 className='mt-2 text-4xl font-heading'>Bitcoin Bastion Public Status</h1>
          <p className='mt-3 max-w-3xl text-bb-gray'>
            This page reports public service posture. Degraded and fallback states are shown explicitly.
          </p>
        </header>

        <section className='bastion-card'>
          <h2 className='text-xl font-heading'>Bastion Live Status Orb</h2>
          <div className='mt-4 flex items-center gap-4'>
            <div aria-label='live status orb' className={`h-5 w-5 rounded-full ${orbTone === 'good' ? 'bg-bb-success' : orbTone === 'warn' ? 'bg-bb-warning' : 'bg-bb-gray'}`} />
            <StatusPill
              label={
                isFallback
                  ? 'Website online · Backend status unknown'
                  : publicStatus.data?.platform_status ?? 'unknown'
              }
              tone={orbTone}
            />
          </div>
          {loading && <p className='mt-3 text-sm text-bb-gray'>Loading status signals…</p>}
        </section>

        <section className='grid gap-4 lg:grid-cols-2'>
          <article className='bastion-card'>
            <h3 className='font-heading text-lg'>Platform status</h3>
            <p className='mt-2 text-sm'>Platform: {publicStatus.data?.platform_status ?? 'unknown'}</p>
            <p className='text-sm'>Trace: {publicStatus.data?.trace_status ?? 'unknown'}</p>
            <p className='text-sm'>Production calibrated: {publicStatus.data?.production_calibrated ? 'Yes' : 'No'}</p>
          </article>

          <article className='bastion-card'>
            <h3 className='font-heading text-lg'>Health checks</h3>
            <ul className='mt-2 space-y-1 text-sm'>
              <li>/health: {health.data?.status ?? 'unknown'}</li>
              <li>/health/live: {live.data?.status ?? 'unknown'}</li>
              <li>/health/ready: {ready.data?.status ?? 'unknown'}</li>
            </ul>
          </article>
        </section>

        <section className='bastion-card'>
          <h3 className='font-heading text-lg'>Module matrix</h3>
          <div className='mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-3'>
            {Object.entries(publicStatus.data?.modules ?? {}).map(([k, v]) => (
              <div key={k} className='rounded-lg border p-3 text-sm'>
                <p className='font-semibold'>{k}</p>
                <p className='text-bb-gray'>{v}</p>
              </div>
            ))}
            {!Object.keys(publicStatus.data?.modules ?? {}).length && (
              <p className='text-sm text-bb-gray'>Module telemetry unavailable in fallback/degraded mode.</p>
            )}
          </div>
        </section>

        <section className='grid gap-4 lg:grid-cols-2'>
          <article className='bastion-card'>
            <h3 className='font-heading text-lg'>Known limitations</h3>
            <ul className='mt-2 list-disc space-y-1 pl-5 text-sm'>
              {(publicStatus.data?.known_limitations ?? []).map((x) => <li key={x}>{x}</li>)}
              {(publicStats.data?.limitations ?? []).map((x) => <li key={x}>{x}</li>)}
            </ul>
          </article>

          <article className='bastion-card'>
            <h3 className='font-heading text-lg'>Stats panel</h3>
            <ul className='mt-2 space-y-1 text-sm'>
              <li>Reports generated: {publicStats.data?.reports_generated ?? 0}</li>
              <li>Proof packets: {publicStats.data?.proof_packets_generated ?? 0}</li>
              <li>Watchtower entries: {publicStats.data?.watchtower_entries ?? 0}</li>
              <li>Runtime events: {publicStats.data?.runtime_events ?? 0}</li>
            </ul>
            <p className='mt-3 text-xs text-bb-gray'>Supported modules: {(publicStats.data?.supported_modules ?? []).join(', ') || 'n/a'}</p>
          </article>
        </section>

        <section className='rounded-xl border border-bb-border bg-bb-bg-soft p-4 text-sm'>
          <p><strong>Last updated:</strong> {publicStatus.data?.last_update ?? 'unknown'}</p>
          <p className='mt-2'><strong>Degraded/fallback explanation:</strong> If backend APIs are unreachable, this page remains online and reports backend status as unknown. This does not imply backend failure; it indicates status could not be confirmed from the browser at request time.</p>
        </section>
      </div>
    </div>
  );
}
