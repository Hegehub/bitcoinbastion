import type { Metadata } from 'next';
import { ManifestoReader } from '@/components/manifesto/ManifestoReader';

export const metadata: Metadata = {
  title: 'Bitcoin Bastion Manifesto',
  description:
    'Principles for Bitcoin-first, no-custody, evidence-driven infrastructure with operator control and production-grade transparency.',
  openGraph: {
    title: 'Bitcoin Bastion Manifesto',
    description:
      'A serious editorial manifesto covering sovereignty, no-custody design, visible degraded states, and proven production readiness.',
    type: 'article',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Bitcoin Bastion Manifesto',
    description:
      'Bitcoin-first principles: no custody, evidence over claims, operator control, and visible degraded states.',
  },
};

export default function ManifestoPage() {
  return <ManifestoReader />;
}
