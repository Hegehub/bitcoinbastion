import Link from 'next/link';
import type { ProductEntry } from '@/lib/content/products';

export function ProductCard({ product }: { product: ProductEntry }) {
  return (
    <article className='bastion-card'>
      <p className='text-xs uppercase tracking-wide text-bb-gray'>{product.status}</p>
      <h3 className='mt-2 text-xl font-heading'>{product.name}</h3>
      <p className='mt-3 text-bb-gray'>{product.description}</p>
      <Link href={`/products/${product.slug}`} className='mt-4 inline-block rounded-lg border border-bb-border px-3 py-2 text-sm'>
        Open product page
      </Link>
    </article>
  );
}
