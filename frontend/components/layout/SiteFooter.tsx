import Link from 'next/link';

const FOOTER_COLUMNS = [
  { title: 'Product', links: [['Products', '/platform'], ['Status', '/status'], ['Roadmap', '/roadmap']] },
  { title: 'Developers', links: [['Docs', '/docs'], ['Developers', '/developers'], ['Evidence', '/evidence']] },
  { title: 'Operators', links: [['Self-host', '/operations'], ['Security', '/security'], ['View Status', '/status']] },
  { title: 'Project', links: [['Manifesto', '/manifesto'], ['Roadmap', '/roadmap'], ['Bitcoin Bastion', '/']] },
  { title: 'Legal/Safety', links: [['Security', '/security'], ['Advisory only', '/security'], ['No custody', '/security']] },
] as const;

export function SiteFooter() {
  return (
    <footer className='border-t border-bb-border bg-bb-bg-soft'>
      <div className='bastion-container py-12'>
        <div className='grid gap-8 sm:grid-cols-2 lg:grid-cols-5'>
          {FOOTER_COLUMNS.map((col) => (
            <section key={col.title}>
              <h2 className='font-heading text-sm font-semibold text-bb-black'>{col.title}</h2>
              <ul className='mt-3 space-y-2'>
                {col.links.map(([label, href]) => (
                  <li key={label}>
                    <Link href={href} className='text-sm text-bb-graphite hover:text-bb-orange'>
                      {label}
                    </Link>
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </div>
      </div>
    </footer>
  );
}
