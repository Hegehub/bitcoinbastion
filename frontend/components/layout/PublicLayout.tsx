import type { ReactNode } from 'react';

export function PublicLayout({ children }: { children: ReactNode }) {
  return <div className='bastion-container bastion-section'>{children}</div>;
}
