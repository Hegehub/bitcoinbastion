'use client';

import Link from 'next/link';
import { useState } from 'react';
import { BastionCommandPalette } from '@/components/interactive/BastionCommandPalette';
import { LanguageSelector } from '@/components/navigation/LanguageSelector';
import { TRANSLATIONS, type SiteLanguage } from '@/lib/i18n';

export function SiteHeader({ language = 'en' }: { language?: SiteLanguage }) {
  const [open, setOpen] = useState(false);
  const t = TRANSLATIONS[language];
  const navItems = [
    { label: t.nav.platform, href: '/platform' },
    { label: t.nav.trace, href: '/trace' },
    { label: t.nav.evidence, href: '/evidence' },
    { label: t.nav.status, href: '/status' },
    { label: t.nav.developers, href: '/developers' },
    { label: t.nav.operations, href: '/operations' },
    { label: t.nav.docs, href: '/docs' },
    { label: t.nav.security, href: '/security' },
    { label: t.nav.roadmap, href: '/roadmap' },
  ] as const;

  return (
    <header className='sticky top-0 z-40 border-b border-bb-border bg-white/95 backdrop-blur'>
      <div className='bastion-container flex min-h-16 items-center justify-between gap-4'>
        <Link href='/' className='font-heading text-lg font-semibold text-bb-black'>Bitcoin Bastion</Link>
        <nav aria-label={t.accessibility.desktopNavigation} className='hidden items-center gap-5 lg:flex'>
          {navItems.map((item) => <Link key={item.href} href={item.href} className='text-sm text-bb-graphite hover:text-bb-orange'>{item.label}</Link>)}
        </nav>
        <div className='hidden items-center gap-3 lg:flex'>
          <LanguageSelector value={language} label={t.cta.language} />
          <BastionCommandPalette />
          <Link href='/status' className='rounded-xl border border-bb-border px-3 py-2 text-sm font-medium'>{t.cta.viewStatus}</Link>
          <Link href='/operations' className='rounded-xl bg-bb-orange px-3 py-2 text-sm font-semibold text-white'>{t.cta.selfHostBastion}</Link>
        </div>
        <div className='lg:hidden'><BastionCommandPalette /></div>
        <button type='button' className='rounded-lg border border-bb-border px-3 py-2 text-sm lg:hidden' aria-expanded={open} aria-controls='mobile-nav' onClick={() => setOpen((v) => !v)}>{t.cta.menu}</button>
      </div>

      {open ? (
        <nav id='mobile-nav' aria-label={t.accessibility.mobileNavigation} className='border-t border-bb-border bg-white lg:hidden'>
          <div className='bastion-container flex flex-col py-3'>
            <div className='mb-2'><LanguageSelector value={language} label={t.cta.language} /></div>
            {navItems.map((item) => (
              <Link key={item.href} href={item.href} className='rounded-md px-2 py-2 text-sm text-bb-graphite hover:bg-bb-bg-soft hover:text-bb-black' onClick={() => setOpen(false)}>{item.label}</Link>
            ))}
            <div className='mt-2 grid grid-cols-1 gap-2 sm:grid-cols-2'>
              <Link href='/status' className='rounded-lg border border-bb-border px-3 py-2 text-sm font-medium'>{t.cta.viewStatus}</Link>
              <Link href='/operations' className='rounded-lg bg-bb-orange px-3 py-2 text-sm font-semibold text-white'>{t.cta.selfHostBastion}</Link>
            </div>
          </div>
        </nav>
      ) : null}
    </header>
  );
}
