'use client';

import { useState } from 'react';

const MODES = ['Beginner', 'Business', 'Developer', 'Operator', 'Researcher'] as const;

export function ProtocolModeSwitcher() {
  const [mode, setMode] = useState<(typeof MODES)[number]>('Operator');
  return (
    <section className='bastion-card'>
      <h2 className='text-lg font-heading'>Protocol Mode</h2>
      <div className='mt-3 flex flex-wrap gap-2'>
        {MODES.map((m) => (
          <button key={m} type='button' onClick={() => setMode(m)} className={`rounded-full border px-3 py-1 text-sm ${mode === m ? 'border-bb-orange bg-bb-orange-soft' : 'border-bb-border'}`}>
            {m}
          </button>
        ))}
      </div>
      <p className='mt-3 text-sm text-bb-gray'>Current mode: {mode}</p>
    </section>
  );
}
