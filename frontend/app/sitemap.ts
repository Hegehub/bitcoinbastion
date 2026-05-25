import type { MetadataRoute } from 'next';

const routes = [
  '/',
  '/manifesto',
  '/status',
  '/evidence',
  '/security',
  '/self-host',
  '/self-host/quickstart',
  '/self-host/docker',
  '/self-host/kubernetes',
  '/self-host/vps',
  '/self-host/security-checklist',
  '/self-host/production-readiness',
  '/products',
  '/products/core',
  '/products/register',
  '/products/api',
  '/products/evidence-layer',
  '/products/desktop-ai',
  '/products/home-ai',
  '/products/bastion-os',
  '/products/sovereign-grid',
  '/products/crypto-analytics-bot',
  '/developers',
  '/developers/api',
  '/developers/examples',
  '/developers/webhooks',
  '/developers/contributing',
  '/developers/changelog',
  '/roadmap',
  '/genesis',
  '/blog',
  '/design-system',
];

export default function sitemap(): MetadataRoute.Sitemap {
  const baseUrl = 'https://bitcoinbastion.org';
  return routes.map((route) => ({
    url: `${baseUrl}${route}`,
    lastModified: new Date(),
    changeFrequency: 'weekly',
    priority: route === '/' ? 1 : 0.7,
  }));
}
