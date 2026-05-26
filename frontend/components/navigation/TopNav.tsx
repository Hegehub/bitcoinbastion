'use client'
import React from 'react'
import Link from 'next/link';
import { TRANSLATIONS, type SiteLanguage } from '@/lib/i18n';

export function TopNav({ language = 'en' }: { language?: SiteLanguage }) {
  const t = TRANSLATIONS[language];
  return <nav aria-label={t.accessibility.mainNavigation} className='p-4 border-b'><div className='flex gap-4 flex-wrap'><Link href='/platform'>{t.nav.platform}</Link><Link href='/citadel'>{t.nav.citadel}</Link><Link href='/trace'>{t.nav.trace}</Link><Link href='/treasury'>{t.nav.treasury}</Link><Link href='/register'>{t.nav.register}</Link><Link href='/developers'>{t.nav.developers}</Link><Link href='/operations'>{t.nav.operations}</Link><Link href='/security'>{t.nav.security}</Link><Link href='/status'>{t.nav.status}</Link><Link href='/docs'>{t.nav.docs}</Link></div></nav>
}
