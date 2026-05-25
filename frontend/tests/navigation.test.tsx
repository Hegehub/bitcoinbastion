import React from 'react';
import { render, screen } from '@testing-library/react';
import { SiteHeader } from '@/components/navigation/SiteHeader';

test('navigation includes key routes', () => {
  render(<SiteHeader />);
  expect(screen.getByRole('link', { name: 'Products' })).toBeTruthy();
  expect(screen.getByRole('link', { name: 'Developers' })).toBeTruthy();
  expect(screen.getByRole('link', { name: 'Status' })).toBeTruthy();
});
