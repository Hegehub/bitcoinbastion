import Link from 'next/link';
import { ReadinessWizard } from '@/components/selfhost/ReadinessWizard';

const profiles = [
  ['Starter', 'Single host baseline for evaluation and non-critical operations.'],
  ['Operator', 'Multi-service VPS with explicit monitoring, backup, and incident procedures.'],
  ['Production', 'Hardened deployment posture with verified readiness gates and recovery drills.'],
  ['Sovereign', 'Operator-owned stack with Bitcoin-node-aligned controls and minimized external trust.'],
] as const;

export default function SelfHostPage() {
  return (
    <div className='bastion-section'>
      <div className='bastion-container space-y-6'>
        <header>
          <p className='bastion-eyebrow'>Self-host</p>
          <h1 className='mt-2 text-4xl font-heading'>Operate Bitcoin Bastion on infrastructure you control</h1>
          <p className='mt-3 max-w-3xl text-bb-gray'>
            Self-hosting is a sovereignty decision: no custody, no key management by Bastion, and visible degraded states when dependencies fail.
          </p>
        </header>

        <section className='rounded-xl border border-bb-warning bg-bb-orange-soft p-4 text-sm'>
          <strong>No-custody warning:</strong> never store seed phrases, private keys, or signing authority in Bitcoin Bastion.
        </section>

        <section className='grid gap-4 md:grid-cols-2'>
          {profiles.map(([name, desc]) => (
            <article key={name} className='bastion-card'>
              <h2 className='text-xl font-heading'>{name}</h2>
              <p className='mt-2 text-bb-gray'>{desc}</p>
            </article>
          ))}
        </section>

        <ReadinessWizard />

        <section className='bastion-card'>
          <h2 className='text-xl font-heading'>Self-host docs</h2>
          <div className='mt-3 flex flex-wrap gap-2'>
            <Link href='/self-host/quickstart' className='rounded border px-3 py-1 text-sm'>Quickstart</Link>
            <Link href='/self-host/docker' className='rounded border px-3 py-1 text-sm'>Docker</Link>
            <Link href='/self-host/kubernetes' className='rounded border px-3 py-1 text-sm'>Kubernetes</Link>
            <Link href='/self-host/vps' className='rounded border px-3 py-1 text-sm'>VPS</Link>
            <Link href='/self-host/security-checklist' className='rounded border px-3 py-1 text-sm'>Security checklist</Link>
            <Link href='/self-host/production-readiness' className='rounded border px-3 py-1 text-sm'>Production readiness</Link>
          </div>
        </section>
      </div>
    </div>
  );
}
