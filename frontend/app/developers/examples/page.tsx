import { CodeBlock } from '@/components/developers/CodeBlock';

const base = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

export default function DevelopersExamplesPage() {
  return (
    <div className='bastion-section'>
      <div className='bastion-container space-y-6'>
        <h1 className='text-4xl font-heading'>Developer Examples</h1>
        <p className='text-bb-gray'>Reference snippets for public endpoint usage with fallback-safe handling.</p>

        <CodeBlock language='ts' code={`// Fetch public status\nconst status = await fetch('${base}/api/v1/public/status').then(r => r.json());\nconsole.log(status.data.platform_status);`} />
        <CodeBlock language='ts' code={`// Fetch feature catalog\nconst features = await fetch('${base}/api/v1/public/features').then(r => r.json());\nconsole.log(features.data.length);`} />
        <CodeBlock language='ts' code={`// Fetch roadmap\nconst roadmap = await fetch('${base}/api/v1/public/roadmap').then(r => r.json());\nconsole.log(roadmap.data.current_phase);`} />
        <CodeBlock language='ts' code={`// Fallback handling\nasync function getStatus() {\n  try {\n    const res = await fetch('${base}/api/v1/public/status');\n    if (!res.ok) throw new Error('status failed');\n    return (await res.json()).data;\n  } catch {\n    return { platform_status: 'unknown', trace_status: 'unknown' };\n  }\n}`} />
      </div>
    </div>
  );
}
