import React from 'react'
import { ReactNode } from 'react';
import { TopNav } from '../navigation/TopNav';
export function PublicLayout({children}:{children:ReactNode}){return <div className='min-h-screen'><TopNav/><main className='max-w-5xl mx-auto p-4'>{children}</main><footer className='p-4 text-sm text-[var(--muted)]'>Advisory only · No custody</footer></div>}
