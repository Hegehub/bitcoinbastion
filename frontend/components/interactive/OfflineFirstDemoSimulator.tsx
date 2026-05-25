'use client';

import { useMemo, useState } from 'react';

export function OfflineFirstDemoSimulator() {
  const [internet, setInternet] = useState(true);
  const [wifi, setWifi] = useState(true);
  const [bluetooth, setBluetooth] = useState(false);
  const [lightning, setLightning] = useState(true);

  const paymentIntent = useMemo(() => {
    if (!internet && !wifi) return 'deferred';
    if ((internet || wifi) && lightning) return 'synced';
    return 'created';
  }, [internet, wifi, lightning]);

  function toggle(label: string, value: boolean, fn: (v: boolean) => void) {
    return (
      <label className='flex items-center justify-between rounded-lg border p-3 text-sm'>
        <span>{label}</span>
        <button type='button' onClick={() => fn(!value)} className='rounded border px-2 py-1'>
          {value ? 'ON' : 'OFF'}
        </button>
      </label>
    );
  }

  return (
    <section className='bastion-card'>
      <h2 className='text-lg font-heading'>Offline-first Demo Simulator</h2>
      <div className='mt-3 grid gap-2 sm:grid-cols-2'>
        {toggle('Internet', internet, setInternet)}
        {toggle('Local Wi-Fi', wifi, setWifi)}
        {toggle('Bluetooth', bluetooth, setBluetooth)}
        {toggle('Local Lightning Node', lightning, setLightning)}
      </div>
      <p className='mt-3 text-sm'>Payment Intent: <strong className='uppercase'>{paymentIntent}</strong></p>
      <p className='mt-2 text-xs text-bb-gray'>Demo simulator only. No real payments or custody actions occur.</p>
    </section>
  );
}
