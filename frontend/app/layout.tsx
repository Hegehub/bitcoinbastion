import React from 'react'
import './globals.css'

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang='en'><body><a href='#main-content' className='sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 bg-black text-white p-2'>Skip to content</a>{children}</body></html>
}
