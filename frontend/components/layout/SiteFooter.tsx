import Link from 'next/link';
import { TRANSLATIONS, type SiteLanguage } from '@/lib/i18n';

export function SiteFooter({ language = 'en' }: { language?: SiteLanguage }) {
  const t = TRANSLATIONS[language];
  const footerColumns = [
    { title: t.footer.product, links: [[t.nav.products, '/platform'], [t.nav.status, '/status'], [t.nav.roadmap, '/roadmap']] },
    { title: t.nav.developers, links: [[t.nav.docs, '/docs'], [t.nav.developers, '/developers'], [t.nav.evidence, '/evidence']] },
    { title: t.footer.operators, links: [[t.nav.selfHost, '/operations'], [t.nav.security, '/security'], [t.cta.viewStatus, '/status']] },
    { title: t.footer.project, links: [[t.nav.manifesto, '/manifesto'], [t.nav.roadmap, '/roadmap'], ['Bitcoin Bastion', '/']] },
    { title: t.footer.legalSafety, links: [[t.nav.security, '/security'], [t.footer.advisoryOnly, '/security'], [t.footer.noCustody, '/security']] },
  ] as const;

  return (
    <footer className='border-t border-bb-border bg-bb-bg-soft'>
      <div className='bastion-container py-12'>
        <div className='grid gap-8 sm:grid-cols-2 lg:grid-cols-5'>
          {footerColumns.map((col) => (
            <section key={col.title}>
              <h2 className='font-heading text-sm font-semibold text-bb-black'>{col.title}</h2>
              <ul className='mt-3 space-y-2'>
                {col.links.map(([label, href]) => (
                  <li key={label}><Link href={href} className='text-sm text-bb-graphite hover:text-bb-orange'>{label}</Link></li>
                ))}
              </ul>
            </section>
          ))}
        </div>
      </div>
    </footer>
  );
}
