import Link from 'next/link';
import type { ProductEntry } from '@/lib/content/products';

export function ProductDetail({ product }: { product: ProductEntry }) {
  return (
    <div className='bastion-section'>
      <div className='bastion-container'>
        <p className='bastion-eyebrow'>Products</p>
        <h1 className='mt-3 text-4xl font-heading'>{product.name}</h1>
        <p className='mt-2 text-sm uppercase text-bb-gray'>Status: {product.status}</p>
        <p className='mt-4 max-w-3xl text-bb-gray'>{product.description}</p>

        <div className='mt-8 grid gap-4 lg:grid-cols-2'>
          <section className='bastion-card'><h2 className='font-heading text-xl'>Target users</h2><ul className='mt-3 list-disc pl-5'>{product.targetUsers.map((x)=><li key={x}>{x}</li>)}</ul></section>
          <section className='bastion-card'><h2 className='font-heading text-xl'>Core capabilities</h2><ul className='mt-3 list-disc pl-5'>{product.coreCapabilities.map((x)=><li key={x}>{x}</li>)}</ul></section>
          <section className='bastion-card'><h2 className='font-heading text-xl'>No-custody / security notes</h2><ul className='mt-3 list-disc pl-5'>{product.securityNotes.map((x)=><li key={x}>{x}</li>)}</ul></section>
          <section className='bastion-card'><h2 className='font-heading text-xl'>Ecosystem relation</h2><p className='mt-3 text-bb-gray'>{product.ecosystemRelation}</p><p className='mt-3 text-sm text-bb-gray'>Roadmap stage: {product.roadmapStage}</p></section>
        </div>

        <div className='mt-8 flex gap-3'>
          <Link href={product.cta.href} className='rounded-xl bg-bb-orange px-4 py-2 font-semibold text-white'>{product.cta.label}</Link>
          <Link href='/products' className='rounded-xl border border-bb-border px-4 py-2'>All products</Link>
        </div>
      </div>
    </div>
  );
}
