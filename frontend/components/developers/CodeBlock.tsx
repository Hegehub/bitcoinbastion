'use client';

import { useState } from 'react';

export function CodeBlock({ code, language = 'text' }: { code: string; language?: string }) {
  const [copied, setCopied] = useState(false);

  async function onCopy() {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 1200);
    } catch {
      setCopied(false);
    }
  }

  return (
    <div className='overflow-hidden rounded-xl border border-bb-border bg-bb-black'>
      <div className='flex items-center justify-between border-b border-white/10 px-3 py-2'>
        <span className='font-mono text-xs text-white/70'>{language}</span>
        <button type='button' onClick={onCopy} className='rounded border border-white/20 px-2 py-1 text-xs text-white'>
          {copied ? 'Copied' : 'Copy'}
        </button>
      </div>
      <pre className='overflow-x-auto p-4 font-mono text-sm text-white'>
        <code>{code}</code>
      </pre>
    </div>
  );
}
