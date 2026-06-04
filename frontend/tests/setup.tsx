import React from 'react';
import { afterEach, vi } from 'vitest';
import { cleanup } from '@testing-library/react';

vi.mock('next/link', () => ({
  default: ({ href, children, ...props }: any) => {
    return (
      // eslint-disable-next-line jsx-a11y/anchor-has-content
      <a href={typeof href === 'string' ? href : '#'} {...props}>{children}</a>
    );
  },
}));


vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), refresh: vi.fn(), prefetch: vi.fn() }),
  usePathname: () => '/',
  useSearchParams: () => new URLSearchParams(),
}));

afterEach(() => cleanup());
