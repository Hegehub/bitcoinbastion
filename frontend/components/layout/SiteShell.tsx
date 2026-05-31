import type { ReactNode } from 'react';
import { LanguageRuntimeTranslator } from '@/components/i18n/LanguageRuntimeTranslator';
import { SiteFooter } from './SiteFooter';
import { SiteHeader } from '../navigation/SiteHeader';
import { TRANSLATIONS, type SiteLanguage } from '@/lib/i18n';

export function SiteShell({ children, language = 'en' }: { children: ReactNode; language?: SiteLanguage }) {
  const t = TRANSLATIONS[language];

  return (
    <div className='min-h-screen bg-bb-bg text-bb-black'>
      <a
        href='#main-content'
        className='sr-only z-50 rounded-md bg-bb-black px-3 py-2 text-white focus:not-sr-only focus:absolute focus:left-4 focus:top-4'
      >
        {t.accessibility.skipToContent}
      </a>
      <LanguageRuntimeTranslator language={language} />
      <SiteHeader language={language} />
      <main id='main-content' className='bastion-gradient-grid'>
        {children}
      </main>
      <SiteFooter language={language} />
    </div>
  );
}
