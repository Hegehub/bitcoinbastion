'use client';

import { usePublicRoadmap } from '@/hooks/usePublicRoadmap';

function Bucket({ title, items }: { title: string; items: string[] }) {
  return (
    <article className='bastion-card'>
      <h2 className='text-xl font-heading'>{title}</h2>
      <ul className='mt-3 list-disc space-y-1 pl-5 text-sm text-bb-graphite'>
        {items.length ? items.map((i) => <li key={i}>{i}</li>) : <li>None reported.</li>}
      </ul>
    </article>
  );
}

export default function RoadmapPage() {
  const roadmap = usePublicRoadmap();
  const data = roadmap.data;

  return (
    <div className='bastion-section'>
      <div className='bastion-container space-y-6'>
        <header>
          <p className='bastion-eyebrow'>Roadmap</p>
          <h1 className='mt-2 text-4xl font-heading'>Public Roadmap</h1>
          <p className='mt-3 max-w-3xl text-bb-gray'>Status language reflects backend public roadmap outputs and should not be interpreted as blanket production certification.</p>
        </header>

        <section className='bastion-card'>
          <p className='text-sm uppercase text-bb-gray'>Current phase</p>
          <p className='mt-1 text-2xl font-heading'>{data?.current_phase ?? 'baseline'}</p>
          {roadmap.isLoading && <p className='mt-2 text-sm text-bb-gray'>Loading roadmap signal…</p>}
        </section>

        <section className='grid gap-4 lg:grid-cols-2'>
          <Bucket title='Implemented' items={data?.implemented ?? []} />
          <Bucket title='Baseline' items={data?.baseline ?? []} />
          <Bucket title='Placeholder' items={data?.placeholder ?? []} />
          <Bucket title='Planned' items={data?.planned ?? []} />
          <Bucket title='Not started' items={data?.not_started ?? []} />
        </section>
      </div>
    </div>
  );
}
