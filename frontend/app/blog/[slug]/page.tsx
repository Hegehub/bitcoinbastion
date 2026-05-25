import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { BLOG_POSTS, getPost } from '@/lib/content/blog';

export function generateStaticParams() {
  return BLOG_POSTS.map((p) => ({ slug: p.slug }));
}

export function generateMetadata({ params }: { params: { slug: string } }): Metadata {
  const post = getPost(params.slug);
  if (!post) return { title: 'Post not found' };
  return { title: post.title, description: post.description };
}

export default function BlogPostPage({ params }: { params: { slug: string } }) {
  const post = getPost(params.slug);
  if (!post) return notFound();

  return (
    <div className='bastion-section'>
      <div className='bastion-container max-w-4xl space-y-5'>
        <p className='bastion-eyebrow'>Blog</p>
        <h1 className='text-4xl font-heading'>{post.title}</h1>
        <p className='text-sm text-bb-gray'>{post.publishedAt}</p>
        {post.body.map((p, idx) => (
          <p key={idx} className='text-bb-graphite'>{p}</p>
        ))}
      </div>
    </div>
  );
}
