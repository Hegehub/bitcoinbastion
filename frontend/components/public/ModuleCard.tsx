import React from 'react'
import Link from 'next/link'
import { StatusBadge } from '../ui/StatusBadge'
export function ModuleCard({title,href,status,summary}:{title:string;href:string;status:string;summary:string}){return <Link href={href} className='block border rounded p-4 space-y-2'><div className='flex justify-between'><h3 className='font-semibold'>{title}</h3><StatusBadge label={status}/></div><p className='text-sm'>{summary}</p></Link>}
