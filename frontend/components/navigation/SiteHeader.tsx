'use client';

import Link from 'next/link';
import { useState } from 'react';

const NAV_ITEMS = [
  { label: 'Products', href: '/platform' },
  { label: 'Developers', href: '/developers' },
  { label: 'Self-host', href: '/operations' },
  { label: 'Manifesto', href: '/manifesto' },
  { label: 'Evidence', href: '/evidence' },
  { label: 'Status', href: '/status' },
  { label: 'Roadmap', href: '/roadmap' },
  { label: 'Security', href: '/security' },
  { label: 'Docs', href: '/docs' },
] as const;

export function SiteHeader() {
  const [open, setOpen] = useState(false);

  return (
    <header className='sticky top-0 z-40 border-b border-bb-border bg-white/95 backdrop-blur'>
      <div className='bastion-container flex min-h-16 items-center justify-between gap-4'>
        <Link href='/' className='font-heading text-lg font-semibold text-bb-black'>
          Bitcoin Bastion
        </Link>

        <nav aria-label='Desktop navigation' className='hidden items-center gap-5 lg:flex'>
          {NAV_ITEMS.map((item) => (
            <Link key={item.href} href={item.href} className='text-sm text-bb-graphite hover:text-bb-orange'>
              {item.label}
            </Link>
          ))}
        </nav>

        <div className='hidden items-center gap-3 lg:flex'>
          <Link href='/status' className='rounded-xl border border-bb-border px-3 py-2 text-sm font-medium'>
            View Status
          </Link>
          <Link href='/operations' className='rounded-xl bg-bb-orange px-3 py-2 text-sm font-semibold text-white'>
            Self-host Bitcoin Bastion
          </Link>
        </div>

        <button
          type='button'
          className='rounded-lg border border-bb-border px-3 py-2 text-sm lg:hidden'
          aria-expanded={open}
          aria-controls='mobile-nav'
          onClick={() => setOpen((v) => !v)}
        >
          Menu
        </button>
      </div>

      {open ? (
        <nav id='mobile-nav' aria-label='Mobile navigation' className='border-t border-bb-border bg-white lg:hidden'>
          <div className='bastion-container flex flex-col py-3'>
            {NAV_ITEMS.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className='rounded-md px-2 py-2 text-sm text-bb-graphite hover:bg-bb-bg-soft hover:text-bb-black'
                onClick={() => setOpen(false)}
              >
                {item.label}
              </Link>
            ))}
            <div className='mt-2 grid grid-cols-1 gap-2 sm:grid-cols-2'>
              <Link href='/status' className='rounded-lg border border-bb-border px-3 py-2 text-sm font-medium'>
                View Status
              </Link>
              <Link href='/operations' className='rounded-lg bg-bb-orange px-3 py-2 text-sm font-semibold text-white'>
                Self-host Bitcoin Bastion
              </Link>
            </div>
          </div>
        </nav>
      ) : null}
    </header>
  );
}
