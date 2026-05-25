import type { ReactNode } from 'react';
import { SiteFooter } from './SiteFooter';
import { SiteHeader } from '../navigation/SiteHeader';

export function SiteShell({ children }: { children: ReactNode }) {
  return (
    <div className='min-h-screen bg-bb-bg text-bb-black'>
      <a
        href='#main-content'
        className='sr-only z-50 rounded-md bg-bb-black px-3 py-2 text-white focus:not-sr-only focus:absolute focus:left-4 focus:top-4'
      >
        Skip to content
      </a>
      <SiteHeader />
      <main id='main-content' className='bastion-gradient-grid'>
        {children}
      </main>
      <SiteFooter />
    </div>
  );
}
