import React from 'react'
import { PublicLayout } from '@/components/layout/PublicLayout';
import { ArchitectureFlow } from '@/components/public/ArchitectureFlow';
import { DeveloperCTA } from '@/components/public/DeveloperCTA';
import { FeatureGrid } from '@/components/public/FeatureGrid';
import { HeroSection } from '@/components/public/HeroSection';
import { NoCustodyNotice } from '@/components/public/NoCustodyNotice';
import { PrincipleCard } from '@/components/public/PrincipleCard';
import { RoadmapPreview } from '@/components/public/RoadmapPreview';
import { SafetyBanner } from '@/components/public/SafetyBanner';
import { StatusStrip } from '@/components/public/StatusStrip';

export default function Home(){const p=['Bitcoin-first','No-custody','Watch-only','Advisory-only','Evidence-based','Operator-controlled'];return <PublicLayout><HeroSection/><StatusStrip/><section className='grid sm:grid-cols-2 md:grid-cols-3 gap-2'>{p.map(i=><PrincipleCard key={i} title={i}/> )}</section><FeatureGrid/><ArchitectureFlow/><SafetyBanner/><NoCustodyNotice/><DeveloperCTA/><RoadmapPreview/></PublicLayout>}
