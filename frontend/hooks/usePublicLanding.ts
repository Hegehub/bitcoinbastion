'use client';
import { useQuery } from '@tanstack/react-query';
import { publicApi } from '@/lib/api/public';

export function usePublicLanding() {
  return useQuery({ queryKey: ['public', 'landing'], queryFn: publicApi.getLanding });
}
