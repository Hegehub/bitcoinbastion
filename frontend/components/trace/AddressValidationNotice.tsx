import React from 'react'
export function AddressValidationNotice({ message }: { message?: string }) { if (!message) return null; return <p role='alert' className='text-sm text-red-400 mt-2'>{message}</p> }
