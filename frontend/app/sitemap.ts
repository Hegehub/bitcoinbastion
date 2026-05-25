import type { MetadataRoute } from 'next';

const routes = [
  '/',
  '/platform',
  '/developers',
  '/developers/api',
  '/developers/examples',
  '/developers/webhooks',
  '/developers/contributing',
  '/developers/changelog',
  '/operations',
  '/manifesto',
  '/evidence',
  '/status',
  '/roadmap',
  '/security',
  '/docs',
  '/design-system',
  '/products',
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
