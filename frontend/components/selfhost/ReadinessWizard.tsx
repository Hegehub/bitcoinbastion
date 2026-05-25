'use client';

import Link from 'next/link';
import { useMemo, useState } from 'react';

type Answers = {
  vps: boolean;
  domain: boolean;
  postgres: boolean;
  redis: boolean;
  telegram: boolean;
  bitcoinNode: boolean;
  kubernetes: boolean;
};

const defaults: Answers = {
  vps: false,
  domain: false,
  postgres: false,
  redis: false,
  telegram: false,
  bitcoinNode: false,
  kubernetes: false,
};

function Choice({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (value: boolean) => void;
}) {
  return (
    <label className='flex items-center justify-between gap-3 rounded-lg border border-bb-border p-3'>
      <span className='text-sm'>{label}</span>
      <select
        aria-label={label}
        className='rounded border border-bb-border bg-white px-2 py-1 text-sm'
        value={checked ? 'yes' : 'no'}
        onChange={(e) => onChange(e.target.value === 'yes')}
      >
        <option value='no'>No</option>
        <option value='yes'>Yes</option>
      </select>
    </label>
  );
}

export function ReadinessWizard() {
  const [a, setA] = useState<Answers>(defaults);

  const result = useMemo(() => {
    if (a.kubernetes) {
      return {
        profile: 'Production',
        services: ['PostgreSQL', 'Redis', 'Kubernetes cluster', 'Ingress + TLS', a.bitcoinNode ? 'Bitcoin node' : 'Bitcoin provider'],
        links: ['/self-host/kubernetes', '/self-host/production-readiness', '/self-host/security-checklist'],
      };
    }

    if (a.vps && a.domain && a.postgres && a.redis) {
      return {
        profile: a.bitcoinNode ? 'Sovereign' : 'Operator',
        services: ['VPS', 'Domain + TLS', 'PostgreSQL', 'Redis', a.bitcoinNode ? 'Bitcoin node integration' : 'Managed Bitcoin provider'],
        links: ['/self-host/vps', '/self-host/docker', '/self-host/security-checklist'],
      };
    }

    if (a.vps) {
      return {
        profile: 'Starter',
        services: ['VPS', 'Docker', 'Basic monitoring', 'Backups'],
        links: ['/self-host/quickstart', '/self-host/docker', '/self-host/security-checklist'],
      };
    }

    return {
      profile: 'Starter',
      services: ['Local dev environment', 'Container runtime', 'Non-production test data'],
      links: ['/self-host/quickstart', '/self-host/security-checklist'],
    };
  }, [a]);

  return (
    <section className='bastion-card'>
      <h2 className='text-2xl font-heading'>Self-Hosted Readiness Wizard</h2>
      <p className='mt-2 text-sm text-bb-gray'>No secrets are requested. This wizard is client-side only and stores nothing sensitive.</p>
      <div className='mt-4 grid gap-3 sm:grid-cols-2'>
        <Choice label='Do you have a VPS?' checked={a.vps} onChange={(v) => setA((x) => ({ ...x, vps: v }))} />
        <Choice label='Do you have a domain?' checked={a.domain} onChange={(v) => setA((x) => ({ ...x, domain: v }))} />
        <Choice label='Do you have PostgreSQL?' checked={a.postgres} onChange={(v) => setA((x) => ({ ...x, postgres: v }))} />
        <Choice label='Do you have Redis?' checked={a.redis} onChange={(v) => setA((x) => ({ ...x, redis: v }))} />
        <Choice label='Do you need Telegram integration?' checked={a.telegram} onChange={(v) => setA((x) => ({ ...x, telegram: v }))} />
        <Choice label='Do you plan Bitcoin node integration?' checked={a.bitcoinNode} onChange={(v) => setA((x) => ({ ...x, bitcoinNode: v }))} />
        <Choice label='Do you need Kubernetes?' checked={a.kubernetes} onChange={(v) => setA((x) => ({ ...x, kubernetes: v }))} />
      </div>

      <div className='mt-6 rounded-xl border border-bb-border bg-bb-bg-soft p-4'>
        <p className='text-xs uppercase tracking-wide text-bb-gray'>Recommended profile</p>
        <p className='mt-1 text-xl font-heading'>{result.profile}</p>
        <p className='mt-3 text-sm font-semibold'>Required services</p>
        <ul className='mt-2 list-disc pl-5 text-sm'>
          {result.services.map((s) => <li key={s}>{s}</li>)}
        </ul>
        <p className='mt-4 text-sm font-semibold'>Security checklist focus</p>
        <ul className='mt-2 list-disc pl-5 text-sm'>
          <li>Never place private keys or seed phrases in Bastion.</li>
          <li>Enable TLS, backups, and restore drills before production cutover.</li>
          <li>Keep degraded mode indicators visible to operators.</li>
        </ul>
        <p className='mt-4 text-sm font-semibold'>Next docs</p>
        <div className='mt-2 flex flex-wrap gap-2'>
          {result.links.map((link) => (
            <Link key={link} href={link} className='rounded border border-bb-border bg-white px-3 py-1 text-sm'>
              {link}
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}
