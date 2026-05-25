import { notFound } from 'next/navigation';
import { ProductDetail } from '@/components/products/ProductDetail';
import { getProduct } from '@/lib/content/products';

export default function ProductPage() {
  const product = getProduct('core');
  if (!product) return notFound();
  return <ProductDetail product={product} />;
}
