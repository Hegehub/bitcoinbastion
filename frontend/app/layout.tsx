import type { Metadata } from 'next';
import type { ReactNode } from 'react';
import { cookies } from 'next/headers';
import { SiteShell } from '@/components/layout/SiteShell';
import { QueryProvider } from '@/components/providers/QueryProvider';
import { getLanguageFromCookie, LANGUAGE_COOKIE_NAME } from '@/lib/i18n';
import './globals.css';

export const metadata: Metadata = {
  metadataBase: new URL('https://bitcoinbastion.org'),
  title: {
    default: 'Bitcoin Bastion',
    template: '%s · Bitcoin Bastion',
  },
  description:
    'Bitcoin Bastion is a security-first, evidence-first platform for advisory Bitcoin intelligence, status transparency, and sovereign operations.',
  openGraph: {
    title: 'Bitcoin Bastion',
    description:
      'Security-first Bitcoin intelligence with transparent status, evidence workflows, and self-host operations guidance.',
    type: 'website',
    siteName: 'Bitcoin Bastion',
    url: 'https://bitcoinbastion.org',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Bitcoin Bastion',
    description:
      'Security-first Bitcoin intelligence with transparent status, evidence workflows, and self-host operations guidance.',
  },
};

export default async function RootLayout({ children }: { children: ReactNode }) {
  const cookieStore = await cookies();
  const language = getLanguageFromCookie(cookieStore.get(LANGUAGE_COOKIE_NAME)?.value);

  return (
    <html lang={language}>
      <body>
        <QueryProvider><SiteShell language={language}>{children}</SiteShell></QueryProvider>
      </body>
    </html>
  );
}
