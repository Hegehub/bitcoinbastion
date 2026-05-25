import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Genesis',
  description: 'Why Bitcoin Bastion exists, what problem it solves, what it refuses to become, and where it is going.',
};

export default function GenesisPage() {
  return (
    <div className='bastion-section'>
      <div className='bastion-container space-y-6'>
        <p className='bastion-eyebrow'>Genesis</p>
        <h1 className='text-4xl font-heading'>Why Bitcoin Bastion exists</h1>

        <section className='bastion-card'>
          <h2 className='text-xl font-heading'>The problem it solves</h2>
          <p className='mt-2 text-bb-gray'>Operators need Bitcoin-native intelligence that is explainable, no-custody, and explicit about degraded states and confidence boundaries.</p>
        </section>

        <section className='bastion-card'>
          <h2 className='text-xl font-heading'>What it refuses to become</h2>
          <p className='mt-2 text-bb-gray'>Bitcoin Bastion is not a custodian, does not manage private keys, and does not claim autonomous authority over signing actions.</p>
        </section>

        <section className='bastion-card'>
          <h2 className='text-xl font-heading'>Where it is going</h2>
          <p className='mt-2 text-bb-gray'>Toward verifiable evidence workflows, stronger operator controls, and clearer production readiness signals grounded in testable artifacts.</p>
        </section>
      </div>
    </div>
  );
}
