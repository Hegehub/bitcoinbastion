import Link from 'next/link';
import { CodeBlock } from '@/components/developers/CodeBlock';

const base = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';
const docsUrl = `${base.replace(/\/$/, '')}/docs`;

export default function DevelopersApiPage() {
  return (
    <div className='bastion-section'>
      <div className='bastion-container space-y-6'>
        <h1 className='text-4xl font-heading'>Developer API Reference</h1>
        <p className='text-bb-gray'>Public endpoints currently available from the backend public surface.</p>

        <section className='bastion-card'>
          <h2 className='font-heading text-xl'>Public endpoints</h2>
          <ul className='mt-3 list-disc space-y-1 pl-5 font-mono text-sm'>
            <li>GET /api/v1/public/landing</li>
            <li>GET /api/v1/public/status</li>
            <li>GET /api/v1/public/roadmap</li>
            <li>GET /api/v1/public/stats</li>
            <li>GET /api/v1/public/features</li>
            <li>GET /api/v1/public/trace/{'{report_id}'}/summary</li>
          </ul>
        </section>

        <section className='grid gap-4 lg:grid-cols-2'>
          <article className='space-y-2'>
            <h3 className='font-heading text-lg'>curl example</h3>
            <CodeBlock language='bash' code={`curl -s ${base}/api/v1/public/status`} />
          </article>
          <article className='space-y-2'>
            <h3 className='font-heading text-lg'>fetch example</h3>
            <CodeBlock language='ts' code={`const res = await fetch('${base}/api/v1/public/status');\nconst body = await res.json();\nconst status = body.data;`} />
          </article>
        </section>

        <section className='bastion-card'>
          <h2 className='font-heading text-xl'>Response envelope</h2>
          <p className='mt-2 text-sm text-bb-gray'>Public responses use the envelope shape below:</p>
          <CodeBlock language='json' code={`{\n  "success": true,\n  "data": { ... }\n}`} />
          <p className='mt-3 text-sm text-bb-gray'>OpenAPI docs: <Link className='underline' href={docsUrl}>{docsUrl}</Link></p>
        </section>
      </div>
    </div>
  );
}
