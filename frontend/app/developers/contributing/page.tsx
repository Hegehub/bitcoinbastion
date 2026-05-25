import { CodeBlock } from '@/components/developers/CodeBlock';

export default function DevelopersContributingPage() {
  return (
    <div className='bastion-section'>
      <div className='bastion-container space-y-6'>
        <h1 className='text-4xl font-heading'>Contributing</h1>
        <p className='text-bb-gray'>Expect production-quality changes with tests, clear scope, and evidence-backed reasoning.</p>

        <section className='bastion-card'>
          <h2 className='font-heading text-xl'>Local setup</h2>
          <CodeBlock language='bash' code={`git clone <repo>\ncd bitcoinbastion`} />
        </section>

        <section className='grid gap-4 lg:grid-cols-2'>
          <article className='bastion-card'>
            <h3 className='font-heading text-lg'>Backend setup</h3>
            <CodeBlock language='bash' code={`python -m venv .venv\nsource .venv/bin/activate\npip install -e .[dev]\npytest -q`} />
          </article>
          <article className='bastion-card'>
            <h3 className='font-heading text-lg'>Frontend setup</h3>
            <CodeBlock language='bash' code={`cd frontend\nnpm install\nnpm run lint\nnpm run typecheck\nnpm run build`} />
          </article>
        </section>

        <section className='bastion-card'>
          <h2 className='font-heading text-xl'>PR expectations</h2>
          <ul className='mt-3 list-disc space-y-1 pl-5 text-sm text-bb-graphite'>
            <li>Do not claim unsupported production functionality.</li>
            <li>Include tests/checks run with outcomes.</li>
            <li>Preserve no-custody and security boundaries.</li>
            <li>Keep docs and contracts aligned with current backend behavior.</li>
          </ul>
        </section>
      </div>
    </div>
  );
}
