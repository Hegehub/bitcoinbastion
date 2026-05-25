export type ProductStatus = 'implemented' | 'baseline' | 'planned' | 'research' | 'concept';

export type ProductEntry = {
  slug: string;
  name: string;
  status: ProductStatus;
  description: string;
  targetUsers: string[];
  coreCapabilities: string[];
  securityNotes: string[];
  ecosystemRelation: string;
  roadmapStage: string;
  cta: { label: string; href: string };
};

export const PRODUCTS: ProductEntry[] = [
  {
    slug: 'core',
    name: 'Bitcoin Bastion Core',
    status: 'baseline',
    description: 'Foundational control plane for advisory Bitcoin intelligence, status, and operator workflows.',
    targetUsers: ['Security teams', 'Bitcoin operators', 'Compliance analysts'],
    coreCapabilities: ['Public status surfaces', 'Risk/evidence workflow primitives', 'Operator-run deployment model'],
    securityNotes: ['No custody by design', 'No seed phrase or private key handling'],
    ecosystemRelation: 'Center of the product constellation; all other modules depend on Core contracts and posture.',
    roadmapStage: 'Baseline platform hardening',
    cta: { label: 'View Core details', href: '/products/core' },
  },
  {
    slug: 'register', name: 'Bitcoin Bastion Register', status: 'planned',
    description: 'Structured register for incidents, policy exceptions, and operational decisions.',
    targetUsers: ['Operations teams', 'Risk managers'], coreCapabilities: ['Decision logging', 'Evidence linkage', 'Review workflows'],
    securityNotes: ['Advisory records only', 'No transaction custody actions'],
    ecosystemRelation: 'Consumes Core evidence and status context for governance trails.', roadmapStage: 'Planned implementation',
    cta: { label: 'Explore Register', href: '/products/register' },
  },
  {
    slug: 'api', name: 'Bitcoin Bastion API', status: 'implemented',
    description: 'FastAPI-based integration surface for public-safe and operator modules.',
    targetUsers: ['Developers', 'Integrators', 'Platform teams'], coreCapabilities: ['Versioned endpoints', 'Typed response contracts', 'Health and status routes'],
    securityNotes: ['Public-safe schemas', 'No private key interfaces'],
    ecosystemRelation: 'Primary integration layer for frontend and ecosystem tools.', roadmapStage: 'Implemented foundation with ongoing hardening',
    cta: { label: 'Explore API product', href: '/products/api' },
  },
  {
    slug: 'evidence-layer', name: 'Bitcoin Bastion Evidence Layer', status: 'baseline',
    description: 'Evidence-centric layer for explainability, provenance, and timeline context.', targetUsers: ['Investigators', 'Audit teams'],
    coreCapabilities: ['Reason-code summaries', 'Evidence packet primitives', 'Confidence annotations'],
    securityNotes: ['No custody scope', 'Explicit limitation surfacing'],
    ecosystemRelation: 'Provides cross-product trust context and verification trails.', roadmapStage: 'Baseline with iterative validation',
    cta: { label: 'Explore Evidence Layer', href: '/products/evidence-layer' },
  },
  {
    slug: 'desktop-ai', name: 'Bastion Desktop AI', status: 'research',
    description: 'Research track for local operator assistant workflows on controlled desktop environments.',
    targetUsers: ['Power operators', 'Security analysts'], coreCapabilities: ['Local briefing synthesis', 'Policy checklist assistance', 'Human-in-the-loop prompts'],
    securityNotes: ['AI must never control seed phrases or private keys', 'Manual confirmation required for risky actions'],
    ecosystemRelation: 'Potential user interface on top of Core and Evidence Layer outputs.', roadmapStage: 'Research and guardrail definition',
    cta: { label: 'View Desktop AI status', href: '/products/desktop-ai' },
  },
  {
    slug: 'home-ai', name: 'Bastion Home AI', status: 'concept',
    description: 'Concept for household-scale advisory posture visibility and safety education.', targetUsers: ['Home users', 'Bitcoin families'],
    coreCapabilities: ['Educational risk prompts', 'Household readiness checklists', 'Advisory notifications'],
    securityNotes: ['No wallet custody', 'No direct key operations'],
    ecosystemRelation: 'Future consumer-facing extension of Bastion principles.', roadmapStage: 'Concept exploration',
    cta: { label: 'Review Home AI concept', href: '/products/home-ai' },
  },
  {
    slug: 'bastion-os', name: 'Bastion OS', status: 'concept',
    description: 'Conceptual sovereign operating environment profile for Bastion-aligned workloads.', targetUsers: ['Infrastructure teams'],
    coreCapabilities: ['Hardened baseline profiles', 'Operational policy templates', 'Recovery-first defaults'],
    securityNotes: ['No custody scope', 'Operator-owned secrets management'],
    ecosystemRelation: 'Would provide secure runtime substrate for Core ecosystem deployments.', roadmapStage: 'Concept and architecture study',
    cta: { label: 'Review Bastion OS concept', href: '/products/bastion-os' },
  },
  {
    slug: 'sovereign-grid', name: 'Bastion Sovereign Grid', status: 'research',
    description: 'Research direction for distributed sovereign operations across multiple controlled nodes.', targetUsers: ['Multi-site operators', 'Enterprise security teams'],
    coreCapabilities: ['Distributed posture visibility', 'Redundant evidence synchronization', 'Control-plane federation models'],
    securityNotes: ['No delegated custody', 'Explicit trust-boundary mapping'],
    ecosystemRelation: 'Potential scale-out architecture for Core and Evidence operations.', roadmapStage: 'Research prototypes',
    cta: { label: 'View Sovereign Grid status', href: '/products/sovereign-grid' },
  },
  {
    slug: 'crypto-analytics-bot', name: 'Crypto Analytics Bot', status: 'planned',
    description: 'Operational bot interface for curated alerts and digest-style summaries.', targetUsers: ['Ops channels', 'Risk desk'],
    coreCapabilities: ['Digest delivery', 'Alert triage cues', 'Policy-aware briefing snippets'],
    securityNotes: ['Advisory-only outputs', 'No signing or secret handling'],
    ecosystemRelation: 'Delivery extension for Core/Trace insights into operator comms channels.', roadmapStage: 'Planned incremental rollout',
    cta: { label: 'Explore bot roadmap', href: '/products/crypto-analytics-bot' },
  },
];

export const CORE_PRODUCT_SLUG = 'core';
export function getProduct(slug: string): ProductEntry | undefined { return PRODUCTS.find((p) => p.slug === slug); }
