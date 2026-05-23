import React from 'react'
import { ModuleCard } from './ModuleCard'
const mods=[['Platform','/platform'],['Citadel','/citadel'],['Trace','/trace'],['Treasury','/treasury'],['Register','/register'],['Security','/security'],['Operations','/operations'],['Developers','/developers']]
export function FeatureGrid(){return <section className='grid md:grid-cols-2 gap-3'>{mods.map(([t,h])=><ModuleCard key={t} title={t} href={h} status='BASELINE' summary='Informational module page shell.'/>)}</section>}
