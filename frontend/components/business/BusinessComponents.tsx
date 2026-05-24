'use client'
import React from 'react'
import { validatePublicBitcoinAddress } from '@/lib/addressValidation'

export const BusinessDashboard = () => <section><h1 className='text-2xl font-bold'>Business Trace Dashboard</h1><p>Business UI is baseline.</p></section>
export function BatchScreeningForm() { const [v,setV]=React.useState(''); const [e,setE]=React.useState(''); return <div><h2>Batch Screening</h2><textarea aria-label='Batch address input' value={v} onChange={(x)=>setV(x.target.value)} className='w-full border p-2' /><button onClick={()=>{const bad=v.split(/\n+/).find(a=>!validatePublicBitcoinAddress(a).valid); setE(bad?'Sensitive wallet material is not accepted. Only public Bitcoin addresses are supported.':'')}}>Validate Batch</button>{e && <p role='alert'>{e}</p>}</div> }
export const BatchResultTable = () => <div><h3>Batch Results</h3><p>No fake counts shown when data unavailable.</p></div>
export const ReviewDeskTable = () => <section><h2>Review Desk</h2><p>Business decision, not legal verdict. No payment is executed by this action.</p></section>
export const ReviewItemPanel = () => <div><h3>Review Item</h3><p>Decision selector baseline.</p></div>
export const OperatorNotesPanel = () => <div><h3>Operator Notes</h3><p>created_by is optional placeholder.</p></div>
export const BusinessPolicyProfileCard = () => <div><h3>Policy Profile</h3><p>Operational recommendations only.</p></div>
export const BusinessPolicyEditor = () => <div><p>Read-only baseline UI if backend editing unavailable.</p></div>
export const BusinessProofPacketActions = () => <div><h3>Proof Packet Actions</h3><ul><li>Create proof packet</li><li>View proof packet</li><li>Export JSON</li><li>Export Markdown</li><li>CSV export for batch</li><li>PDF export not available in baseline.</li></ul><p>advisory-only · not a legal document · not payment authorization · no custody</p></div>
