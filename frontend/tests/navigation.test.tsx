import React from 'react';
import { fireEvent, render, screen, within } from '@testing-library/react';
import { SiteHeader } from '@/components/navigation/SiteHeader';
import { SiteFooter } from '@/components/layout/SiteFooter';

function hrefFor(link: HTMLElement) {
  return link.getAttribute('href');
}

test('desktop navigation includes canonical public routes with Trace prominent', () => {
  render(<SiteHeader />);
  const desktopNav = screen.getByRole('navigation', { name: /desktop navigation/i });

  const expected = [
    ['Platform', '/platform'],
    ['Trace', '/trace'],
    ['Evidence', '/evidence'],
    ['Status', '/status'],
    ['Developers', '/developers'],
    ['Operations', '/operations'],
    ['Docs', '/docs'],
    ['Security', '/security'],
    ['Roadmap', '/roadmap'],
  ] as const;

  for (const [label, href] of expected) {
    expect(hrefFor(within(desktopNav).getByRole('link', { name: label }))).toBe(href);
  }

  const navText = desktopNav.textContent || '';
  expect(navText.indexOf('Trace')).toBeGreaterThan(navText.indexOf('Platform'));
  expect(navText.indexOf('Trace')).toBeLessThan(navText.indexOf('Evidence'));
  expect(desktopNav.querySelector('a[href="/products"]')).toBeNull();
  expect(desktopNav.querySelector('a[href="/self-host"]')).toBeNull();
});

test('mobile navigation includes Trace and closes after selecting a nav item', () => {
  render(<SiteHeader />);

  fireEvent.click(screen.getByRole('button', { name: /menu/i }));
  const mobileNav = screen.getByRole('navigation', { name: /mobile navigation/i });
  const traceLink = within(mobileNav).getByRole('link', { name: 'Trace' });

  expect(hrefFor(traceLink)).toBe('/trace');
  expect(mobileNav.querySelector('a[href="/products"]')).toBeNull();
  expect(mobileNav.querySelector('a[href="/self-host"]')).toBeNull();

  traceLink.addEventListener('click', (event) => event.preventDefault());
  fireEvent.click(traceLink);
  expect(screen.queryByRole('navigation', { name: /mobile navigation/i })).toBeNull();
});

test('footer exposes Trace without stale route hrefs', () => {
  render(<SiteFooter />);
  expect(hrefFor(screen.getByRole('link', { name: 'Trace' }))).toBe('/trace');
  expect(document.body.querySelector('a[href="/products"]')).toBeNull();
  expect(document.body.querySelector('a[href="/self-host"]')).toBeNull();
});
