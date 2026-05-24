import React from 'react'
import { PublicLayout } from '@/components/layout/PublicLayout'
import { AddressCheckForm } from '@/components/trace/AddressCheckForm'

export default function CheckPage() {
  return <PublicLayout><h1 className='text-3xl font-bold'>Bitcoin Address Check</h1><p className='mt-2'>Analyze public Bitcoin address signals related to risk, origin and privacy exposure using Bastion Trace Lite.</p><div className='my-4 p-3 border rounded'><p>Never enter seed phrases, private keys or wallet files.</p><p>Bitcoin Bastion only accepts public Bitcoin addresses.</p><p>Analysis is advisory-only.</p><p>Results are not legal verification or Bitcoin consensus proof.</p></div><AddressCheckForm /><section className='mt-6'><h2 className='text-xl font-semibold'>FAQ</h2><p>This workflow provides a baseline heuristic summary and may be incomplete.</p></section></PublicLayout>
}
