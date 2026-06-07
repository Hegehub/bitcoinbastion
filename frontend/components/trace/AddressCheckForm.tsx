'use client'
import React, { useState } from 'react'
import { AddressInput } from './AddressInput'
import { AddressValidationNotice } from './AddressValidationNotice'
import { validatePublicBitcoinAddress } from '@/lib/addressValidation'
import { apiClient } from '@/services/apiClient'
import { PublicTraceSummary } from '@/types/trace'
import { TraceErrorState } from './TraceErrorState'
import { normalizeApiError } from '@/services/api'
import { TraceLiteResultCard } from './TraceLiteResultCard'
import { TraceLoadingState } from './TraceLoadingState'

export function AddressCheckForm() {
  const [address, setAddress] = useState('')
  const [error, setError] = useState<string>()
  const [loading, setLoading] = useState(false)
  const [summary, setSummary] = useState<PublicTraceSummary | null>(null)

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    const check = validatePublicBitcoinAddress(address)
    if (!check.valid) { setError(check.error); return }
    setError(undefined); setLoading(true); setSummary(null)
    try {
      const lite = await apiClient.checkTraceLite(address)
      const data = await apiClient.getTraceSummary(lite.report_id)
      setSummary(data)
    } catch {
      setError(normalizeApiError(new Error('api_error_unknown')))
    } finally { setLoading(false) }
  }

  const valid = validatePublicBitcoinAddress(address).valid
  return <form onSubmit={onSubmit} className='space-y-3'><AddressInput value={address} onChange={setAddress} /><AddressValidationNotice message={error} /><button aria-label='Submit address check' disabled={!valid || loading} className='px-4 py-2 rounded bg-orange-600 disabled:opacity-50'>Check Address</button>{loading && <TraceLoadingState />}{summary && <TraceLiteResultCard summary={summary} />}{!loading && !summary && !error && <p className='text-sm'>Advisory only. Results are not legal verification.</p>}{error && !loading && <TraceErrorState message={error} />}</form>
}
