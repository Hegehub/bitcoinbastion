'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';

type CommandAction = {
  label: string;
  href: string;
  description?: string;
};

const STATIC_ACTIONS: readonly CommandAction[] = [
  { label: 'Open Platform', href: '/platform' },
  { label: 'Open Operations', href: '/operations' },
  { label: 'Open Trace', href: '/trace', description: 'Advisory-only address intelligence; public Bitcoin addresses only.' },
  { label: 'Check Bitcoin Address', href: '/check', description: 'Start a no-custody public address check.' },
  { label: 'Open Evidence', href: '/evidence' },
  { label: 'Open Status', href: '/status' },
  { label: 'Open Developers', href: '/developers' },
  { label: 'Open Docs', href: '/docs' },
  { label: 'Open Security', href: '/security' },
  { label: 'Open Roadmap', href: '/roadmap' },
  { label: 'Open Console', href: '/console' },
  { label: 'Open Market Intelligence', href: '/market' },
  { label: 'Open Market Timeline', href: '/market/timeline' },
  { label: 'Open Time Machine', href: '/market/time-machine' },
  { label: 'Open Market Signals', href: '/market/signals' },
  { label: 'Open Market Evidence', href: '/market/evidence' },
  { label: 'Open Narratives', href: '/market/narratives' },
  { label: 'Open Sources', href: '/market/sources' },
  { label: 'Open Manifesto', href: '/manifesto' },
] as const;

const SENSITIVE_REPORT_ID_PATTERNS = [
  /seed\s*phrase/i,
  /mnemonic/i,
  /private\s*key/i,
  /\b[xyz]prv/i,
  /wallet\.dat/i,
  /keystore/i,
  /signing\s*material/i,
];

export function getTraceReportIdFromQuery(query: string): string | null {
  const value = query.trim();
  if (!value || value.includes('/') || /^https?:/i.test(value)) return null;
  if (SENSITIVE_REPORT_ID_PATTERNS.some((pattern) => pattern.test(value))) return null;
  if (/^\d{1,18}$/.test(value)) return value;
  return null;
}

function getDynamicTraceActions(query: string): CommandAction[] {
  const reportId = getTraceReportIdFromQuery(query);
  if (!reportId) return [];
  return [
    { label: 'Open Trace Report', href: `/trace/${reportId}`, description: `Open advisory Trace report ${reportId}.` },
    { label: 'Open Proof Packet', href: `/trace/${reportId}/proof-packet`, description: `Open proof packet for Trace report ${reportId}.` },
  ];
}

function actionMatchesQuery(action: CommandAction, query: string) {
  const q = query.toLowerCase().trim();
  if (!q) return true;
  return action.label.toLowerCase().includes(q) || action.href.toLowerCase().includes(q) || action.description?.toLowerCase().includes(q);
}

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
    const dynamicActions = getDynamicTraceActions(query);
    const staticMatches = STATIC_ACTIONS.filter((action) => actionMatchesQuery(action, query));
    return [...dynamicActions, ...staticMatches];
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
              placeholder='Search pages or type a Trace report id'
              className='w-full rounded-lg border border-bb-border px-3 py-2'
            />
            <p className='mt-2 text-xs text-bb-gray'>Trace actions are advisory-only, no-custody, and for public Bitcoin address workflows.</p>
            <ul className='mt-3 space-y-2'>
              {filtered.map((action) => (
                <li key={action.href}>
                  <Link href={action.href} onClick={() => setOpen(false)} className='block rounded-lg border p-3 hover:border-bb-orange'>
                    <p className='font-medium'>{action.label}</p>
                    <p className='text-xs text-bb-gray'>{action.href}</p>
                    {action.description ? <p className='mt-1 text-xs text-bb-gray'>{action.description}</p> : null}
                  </Link>
                </li>
              ))}
              {!filtered.length && <li className='rounded-lg border p-3 text-sm text-bb-gray'>No actions found. Type a report id to open a Trace report.</li>}
            </ul>
          </div>
        </div>
      ) : null}
    </>
  );
}
