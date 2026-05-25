const TOKENS = [
  ['bb-orange', 'var(--bb-orange)'],
  ['bb-orange-soft', 'var(--bb-orange-soft)'],
  ['bb-black', 'var(--bb-black)'],
  ['bb-graphite', 'var(--bb-graphite)'],
  ['bb-gray', 'var(--bb-gray)'],
  ['bb-border', 'var(--bb-border)'],
  ['bb-bg', 'var(--bb-bg)'],
  ['bb-bg-soft', 'var(--bb-bg-soft)'],
  ['bb-success', 'var(--bb-success)'],
  ['bb-warning', 'var(--bb-warning)'],
  ['bb-danger', 'var(--bb-danger)'],
  ['bb-node-blue', 'var(--bb-node-blue)'],
] as const;

export function DesignTokenPreview() {
  return (
    <section className='bastion-section bastion-gradient-grid'>
      <div className='bastion-container'>
        <p className='bastion-eyebrow'>Bitcoin Bastion UI Foundation</p>
        <h1 className='mt-3 text-3xl font-heading text-bb-black sm:text-4xl'>Design system preview</h1>
        <p className='mt-3 max-w-2xl text-bb-gray'>
          A clean, sovereign, evidence-first visual base inspired by Bitcoin-native clarity.
        </p>

        <div className='mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3'>
          {TOKENS.map(([name, color]) => (
            <article key={name} className='bastion-card'>
              <div className='h-20 w-full rounded-xl border' style={{ backgroundColor: color }} />
              <h2 className='mt-4 font-heading text-lg text-bb-black'>{name}</h2>
              <code className='mt-1 block font-mono text-sm text-bb-graphite'>{color}</code>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
