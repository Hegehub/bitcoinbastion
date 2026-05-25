export function BitcoinPurityMeter() {
  const checks = [
    ['Bitcoin Core primary', true],
    ['Alt assets isolated', true],
    ['No custody', true],
    ['No seed/private key access', true],
    ['Human confirmation required', true],
  ] as const;

  return (
    <section className='bastion-card'>
      <h2 className='text-lg font-heading'>Bitcoin Purity Meter</h2>
      <ul className='mt-3 space-y-2'>
        {checks.map(([label, ok]) => (
          <li key={label} className='flex items-center justify-between rounded-lg border p-2 text-sm'>
            <span>{label}</span>
            <span className={`rounded-full px-2 py-0.5 text-xs ${ok ? 'bg-bb-success/20 text-bb-success' : 'bg-bb-warning/20 text-bb-warning'}`}>{ok ? 'PASS' : 'REVIEW'}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
