import { EvidenceDashboard } from '@/components/evidence/EvidenceDashboard';

export default function EvidencePage() {
  return (
    <section className='bastion-section'>
      <div className='bastion-container'>
        <p className='bastion-eyebrow'>Verification</p>
        <h1 className='mt-3 text-4xl font-heading'>Evidence</h1>
        <p className='mt-4 max-w-3xl text-bb-gray'>
          Signature evidence page for public trust posture: modern dashboard views with explicit baseline/demo labels and no production overclaims.
        </p>
        <div className='mt-6'>
          <EvidenceDashboard />
        </div>
      </div>
    </section>
  );
}
