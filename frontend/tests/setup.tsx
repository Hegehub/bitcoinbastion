import React from 'react';
import { vi } from 'vitest';

vi.mock('next/link', () => ({
  default: ({ href, children, ...props }: any) => {
    return (
      // eslint-disable-next-line jsx-a11y/anchor-has-content
      <a href={typeof href === 'string' ? href : '#'} {...props}>{children}</a>
    );
  },
}));
