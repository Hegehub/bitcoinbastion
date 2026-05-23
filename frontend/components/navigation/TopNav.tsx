'use client'
import React from 'react'
import Link from 'next/link';
export function TopNav(){return <nav aria-label='Main navigation' className='p-4 border-b'><div className='flex gap-4 flex-wrap'><Link href='/platform'>Platform</Link><Link href='/citadel'>Citadel</Link><Link href='/trace'>Trace</Link><Link href='/treasury'>Treasury</Link><Link href='/register'>Register</Link><Link href='/developers'>Developers</Link><Link href='/operations'>Operations</Link><Link href='/security'>Security</Link><Link href='/status'>Status</Link><Link href='/docs'>Docs</Link></div></nav>}
