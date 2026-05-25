import React from 'react';

const PRINCIPLES = [
  { title: 'No seed phrases', status: 'Implemented baseline', detail: 'Bitcoin Bastion does not accept, process, or request mnemonic seed phrases.' },
  { title: 'No private key storage', status: 'Implemented baseline', detail: 'Private keys are outside platform scope and must remain in external custody systems.' },
  { title: 'No custodial control', status: 'Implemented baseline', detail: 'The platform is advisory-only and does not hold funds or signing authority.' },
  { title: 'No automatic transaction signing', status: 'Implemented baseline', detail: 'No autonomous signing or broadcast pipeline is provided.' },
  { title: 'Watch-only direction', status: 'Implemented baseline', detail: 'Data surfaces are designed for watch-only intelligence and risk review workflows.' },
  { title: 'PSBT-first future direction', status: 'Planned direction', detail: 'Future integration direction prioritizes PSBT-compatible boundaries with external signers.' },
  { title: 'External signing model', status: 'Planned direction', detail: 'Signing should remain external to Bastion via user-controlled hardware/software signers.' },
  { title: 'Human Confirmation Firewall', status: 'Implemented baseline', detail: 'Risky actions require explicit human confirmation and auditable checkpoints.' },
  { title: 'Policy Engine', status: 'Implemented baseline', detail: 'Policy constraints drive advisory outputs and operational guardrails.' },
  { title: 'Audit Log', status: 'Implemented baseline', detail: 'Operator-relevant events are expected to be captured for review and traceability.' },
  { title: 'Role-based access', status: 'Baseline / evolving', detail: 'Access boundaries are role-oriented and continue maturing with enterprise controls.' },
  { title: 'AI action restrictions', status: 'Implemented baseline', detail: 'AI-assisted flows are constrained from custody operations and key-material interactions.' },
];

export function SecurityModelPage() {
  return (
    <div className='bastion-section'>
      <div className='bastion-container space-y-6'>
        <header>
          <p className='bastion-eyebrow'>Security model</p>
          <h1 className='mt-2 text-4xl font-heading'>Bitcoin Bastion Security</h1>
          <p className='mt-3 max-w-3xl text-bb-gray'>
            A no-custody, operator-controlled model for serious users and developers. Claims below are scoped to baseline reality and clearly mark future capabilities.
          </p>
        </header>

        <section className='rounded-xl border border-bb-warning bg-bb-orange-soft p-4'>
          <h2 className='text-lg font-heading'>No-Custody Visual Seal</h2>
          <p className='mt-2 text-sm'>No seed phrases. No private keys. No custodial control. No automatic transaction signing.</p>
        </section>

        <section className='bastion-card'>
          <h2 className='text-xl font-heading'>Human Confirmation Firewall (demo)</h2>
          <div className='mt-3 grid gap-3 sm:grid-cols-3'>
            <div className='rounded-lg border p-3'><p className='text-xs text-bb-gray'>Step 1</p><p className='font-semibold'>Policy trigger</p><p className='text-sm text-bb-gray'>High-risk condition detected.</p></div>
            <div className='rounded-lg border p-3'><p className='text-xs text-bb-gray'>Step 2</p><p className='font-semibold'>Human review</p><p className='text-sm text-bb-gray'>Operator validates evidence and context.</p></div>
            <div className='rounded-lg border p-3'><p className='text-xs text-bb-gray'>Step 3</p><p className='font-semibold'>Explicit confirmation</p><p className='text-sm text-bb-gray'>Only then can downstream action proceed.</p></div>
          </div>
          <p className='mt-3 text-xs text-bb-gray'>Demo flow for model explanation; not a claim of fully automated production workflow coverage.</p>
        </section>

        <section className='grid gap-4 lg:grid-cols-2'>
          <article className='bastion-card'>
            <h2 className='text-xl font-heading'>Risk Lens cards</h2>
            <div className='mt-3 space-y-2 text-sm'>
              <div className='rounded-lg border p-3'><strong>Custody risk lens:</strong> kept out-of-scope by design.</div>
              <div className='rounded-lg border p-3'><strong>Operational risk lens:</strong> policy + audit + human gates.</div>
              <div className='rounded-lg border p-3'><strong>Model risk lens:</strong> AI assistance restricted from key control.</div>
            </div>
          </article>
          <article className='bastion-card'>
            <h2 className='text-xl font-heading'>Security model diagram</h2>
            <div className='mt-3 rounded-lg border p-4 text-sm'>
              <p><strong>Watch-only data</strong> → <strong>Policy Engine</strong> → <strong>Human Confirmation Firewall</strong> → <strong>External signer (future/required)</strong></p>
              <p className='mt-2 text-bb-gray'>Bastion remains advisory; signing authority stays external.</p>
            </div>
          </article>
        </section>

        <section className='bastion-card'>
          <h2 className='text-xl font-heading'>Security controls and capability status</h2>
          <div className='mt-3 grid gap-3 md:grid-cols-2'>
            {PRINCIPLES.map((p) => (
              <article key={p.title} className='rounded-lg border p-3'>
                <p className='font-semibold'>{p.title}</p>
                <p className='mt-1 text-xs uppercase tracking-wide text-bb-gray'>{p.status}</p>
                <p className='mt-2 text-sm text-bb-gray'>{p.detail}</p>
              </article>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
