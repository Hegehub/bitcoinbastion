import { ProductCard } from '@/components/products/ProductCard';
import { ProductConstellation } from '@/components/products/ProductConstellation';
import { PRODUCTS } from '@/lib/content/products';
import { ProtocolModeSwitcher } from '@/components/interactive/ProtocolModeSwitcher';
import { BitcoinPurityMeter } from '@/components/interactive/BitcoinPurityMeter';

export default function ProductsPage() {
  return (
    <div className='bastion-section'>
      <div className='bastion-container'>
        <p className='bastion-eyebrow'>Ecosystem</p>
        <h1 className='mt-3 text-4xl font-heading'>Bitcoin Bastion Products</h1>
        <p className='mt-3 max-w-3xl text-bb-gray'>
          Clear distinction between implemented, baseline, planned, research, and concept tracks. No custody claims.
        </p>

        <div className='mt-8 grid gap-4 lg:grid-cols-2'><ProtocolModeSwitcher /><BitcoinPurityMeter /></div>

        <div className='mt-8'>
          <ProductConstellation />
        </div>

        <div className='mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-3'>
          {PRODUCTS.map((p) => (
            <ProductCard key={p.slug} product={p} />
          ))}
        </div>
      </div>
    </div>
  );
}
