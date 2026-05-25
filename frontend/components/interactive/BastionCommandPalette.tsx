'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';

const ACTIONS = [
  { label: 'Open Manifesto', href: '/manifesto' },
  { label: 'View Status', href: '/status' },
  { label: 'View Evidence', href: '/evidence' },
  { label: 'Open Products', href: '/products' },
  { label: 'Open Developers', href: '/developers' },
  { label: 'Open Self-host', href: '/self-host' },
] as const;

export function BastionCommandPalette() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setOpen((v) => !v);
      }
      if (e.key === 'Escape') setOpen(false);
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  const filtered = useMemo(() => {
    const q = query.toLowerCase().trim();
    if (!q) return ACTIONS;
    return ACTIONS.filter((a) => a.label.toLowerCase().includes(q) || a.href.includes(q));
  }, [query]);

  return (
    <>
      <button type='button' onClick={() => setOpen(true)} className='rounded-lg border border-bb-border px-3 py-2 text-sm' aria-label='Open command palette'>
        Command <span className='font-mono text-xs text-bb-gray'>⌘K</span>
      </button>
      {open ? (
        <div className='fixed inset-0 z-50 bg-black/30 p-4' role='dialog' aria-modal='true' aria-label='Bastion command palette'>
          <div className='mx-auto mt-16 w-full max-w-2xl rounded-2xl border bg-white p-4 shadow-xl'>
            <input
              autoFocus
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder='Search pages and actions'
              className='w-full rounded-lg border border-bb-border px-3 py-2'
            />
            <ul className='mt-3 space-y-2'>
              {filtered.map((a) => (
                <li key={a.href}>
                  <Link href={a.href} onClick={() => setOpen(false)} className='block rounded-lg border p-3 hover:border-bb-orange'>
                    <p className='font-medium'>{a.label}</p>
                    <p className='text-xs text-bb-gray'>{a.href}</p>
                  </Link>
                </li>
              ))}
              {!filtered.length && <li className='rounded-lg border p-3 text-sm text-bb-gray'>No actions found.</li>}
            </ul>
          </div>
        </div>
      ) : null}
    </>
  );
}
