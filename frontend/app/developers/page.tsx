import Link from 'next/link';

const PUBLIC_ENDPOINTS = [
  '/api/v1/public/landing',
  '/api/v1/public/status',
  '/api/v1/public/roadmap',
  '/api/v1/public/stats',
  '/api/v1/public/features',
  '/api/v1/public/trace/{report_id}/summary',
];

export default function DevelopersPage() {
  return (
    <div className='bastion-section'>
      <div className='bastion-container space-y-6'>
        <header>
          <p className='bastion-eyebrow'>Developers</p>
          <h1 className='mt-2 text-4xl font-heading'>Build verifiable Bitcoin infrastructure interfaces</h1>
          <p className='mt-3 max-w-3xl text-bb-gray'>
            Build dashboards, safety workflows, and public-facing status experiences on top of Bitcoin Bastion public APIs.
          </p>
        </header>

        <section className='bastion-card'>
          <h2 className='text-xl font-heading'>API overview</h2>
          <p className='mt-2 text-bb-gray'>Versioned FastAPI routes under `/api/v1` with advisory-safe public payloads.</p>
          <ul className='mt-3 list-disc space-y-1 pl-5 text-sm'>
            {PUBLIC_ENDPOINTS.map((e) => <li key={e} className='font-mono'>{e}</li>)}
          </ul>
        </section>

        <section className='grid gap-4 md:grid-cols-2'>
          <article className='bastion-card'>
            <h3 className='font-heading text-lg'>Admin endpoints</h3>
            <p className='mt-2 text-sm text-bb-gray'>Placeholder: admin APIs exist but are not part of public unauthenticated documentation.</p>
          </article>
          <article className='bastion-card'>
            <h3 className='font-heading text-lg'>Evidence API direction</h3>
            <p className='mt-2 text-sm text-bb-gray'>Evidence and explainability surfaces are being formalized with conservative public-safe contracts.</p>
          </article>
          <article className='bastion-card'>
            <h3 className='font-heading text-lg'>Policy API direction</h3>
            <p className='mt-2 text-sm text-bb-gray'>Policy endpoints are operator-facing and expected to retain explicit approval and audit constraints.</p>
          </article>
          <article className='bastion-card'>
            <h3 className='font-heading text-lg'>Quick links</h3>
            <div className='mt-3 flex flex-wrap gap-2 text-sm'>
              <Link href='/developers/api' className='rounded border px-3 py-1'>API</Link>
              <Link href='/developers/examples' className='rounded border px-3 py-1'>Examples</Link>
              <Link href='/developers/webhooks' className='rounded border px-3 py-1'>Webhooks</Link>
              <Link href='/developers/contributing' className='rounded border px-3 py-1'>Contributing</Link>
              <Link href='/developers/changelog' className='rounded border px-3 py-1'>Changelog</Link>
            </div>
          </article>
        </section>
      </div>
    </div>
  );
}
