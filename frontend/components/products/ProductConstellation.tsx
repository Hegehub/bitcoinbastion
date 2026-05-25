import Link from 'next/link';
import { CORE_PRODUCT_SLUG, PRODUCTS } from '@/lib/content/products';

export function ProductConstellation() {
  const center = PRODUCTS.find((p) => p.slug === CORE_PRODUCT_SLUG)!;
  const others = PRODUCTS.filter((p) => p.slug !== CORE_PRODUCT_SLUG);

  return (
    <section className='bastion-card'>
      <h2 className='text-2xl font-heading'>Product Constellation</h2>
      <p className='mt-2 text-bb-gray'>Core at the center; ecosystem modules extend outward by readiness stage.</p>

      <div className='relative mt-8 hidden min-h-[480px] items-center justify-center md:flex'>
        <Link href={`/products/${center.slug}`} className='absolute z-10 rounded-full border-4 border-bb-orange bg-white px-6 py-8 text-center font-heading'>
          {center.name}
        </Link>
        {others.map((p, i) => {
          const angle = (i / others.length) * Math.PI * 2;
          const r = 185;
          const x = Math.cos(angle) * r;
          const y = Math.sin(angle) * r;
          return (
            <Link
              key={p.slug}
              href={`/products/${p.slug}`}
              className='absolute w-44 rounded-xl border bg-white p-3 text-center text-sm hover:border-bb-orange'
              style={{ transform: `translate(${x}px, ${y}px)` }}
            >
              <p className='font-semibold'>{p.name}</p>
              <p className='mt-1 text-xs uppercase text-bb-gray'>{p.status}</p>
            </Link>
          );
        })}
      </div>

      <ul className='mt-6 space-y-2 md:hidden'>
        {PRODUCTS.map((p) => (
          <li key={p.slug}>
            <Link href={`/products/${p.slug}`} className='flex items-center justify-between rounded-lg border p-3'>
              <span>{p.name}</span>
              <span className='text-xs uppercase text-bb-gray'>{p.status}</span>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
