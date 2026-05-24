import React from 'react'

export const LoadingState = ({ label = 'Loading…' }: { label?: string }) => <div aria-live='polite' className='border rounded p-3 animate-pulse'>{label}</div>
export const ErrorState = ({ message }: { message: string }) => <div role='alert' className='border border-red-500 rounded p-3'>{message}</div>
export const EmptyState = ({ message }: { message: string }) => <div className='border rounded p-3 text-sm text-[var(--muted)]'>{message}</div>
export const PlaceholderNotice = ({ message }: { message: string }) => <div className='border rounded p-3 text-sm'>{message}</div>
