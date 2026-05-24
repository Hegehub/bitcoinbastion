import React from 'react'

export function AddressInput({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return <input aria-label='Bitcoin address input' className='w-full border rounded p-3' value={value} onChange={(e) => onChange(e.target.value)} placeholder='Example: bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh' />
}
