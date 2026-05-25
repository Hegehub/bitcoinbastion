export type BlogPost = {
  slug: string;
  title: string;
  description: string;
  publishedAt: string;
  body: string[];
};

export const BLOG_POSTS: BlogPost[] = [
  {
    slug: 'why-bitcoin-bastion-exists',
    title: 'Why Bitcoin Bastion exists',
    description: 'A practical origin story focused on operator control, no-custody boundaries, and verifiable posture.',
    publishedAt: '2026-05-25',
    body: [
      'Bitcoin Bastion exists because operators need infrastructure that is explicit about risk and limits.',
      'It is built for advisory intelligence, not custody. That boundary is structural, not marketing language.',
      'The project prioritizes observable system posture, explainable evidence, and human confirmation before risky actions.',
    ],
  },
  {
    slug: 'evidence-over-claims-bitcoin-infrastructure',
    title: 'Evidence over claims in Bitcoin-native infrastructure',
    description: 'Why production readiness must be demonstrated with artifacts, checks, and visible degraded states.',
    publishedAt: '2026-05-25',
    body: [
      'Claims without artifacts degrade trust. Evidence should be inspectable and tied to concrete system behavior.',
      'Baseline and demo outputs must be labeled clearly to avoid overstating maturity.',
      'A serious Bitcoin operations stack should make degraded states visible and keep custody concerns out of scope.',
    ],
  },
];

export function getPost(slug: string): BlogPost | undefined {
  return BLOG_POSTS.find((p) => p.slug === slug);
}
