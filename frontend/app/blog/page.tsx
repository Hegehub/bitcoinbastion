import type { Metadata } from 'next';
import Link from 'next/link';
import { BLOG_POSTS } from '@/lib/content/blog';

export const metadata: Metadata = {
  title: 'Blog',
  description: 'Project narrative and engineering notes for Bitcoin Bastion.',
};

export default function BlogPage() {
  return (
    <div className='bastion-section'>
      <div className='bastion-container space-y-6'>
        <p className='bastion-eyebrow'>Blog</p>
        <h1 className='text-4xl font-heading'>Bitcoin Bastion Writing</h1>
        <div className='grid gap-4'>
          {BLOG_POSTS.map((post) => (
            <article key={post.slug} className='bastion-card'>
              <h2 className='text-2xl font-heading'>{post.title}</h2>
              <p className='mt-1 text-xs text-bb-gray'>{post.publishedAt}</p>
              <p className='mt-3 text-bb-gray'>{post.description}</p>
              <Link className='mt-4 inline-block rounded border px-3 py-1 text-sm' href={`/blog/${post.slug}`}>Read post</Link>
            </article>
          ))}
        </div>
      </div>
    </div>
  );
}
