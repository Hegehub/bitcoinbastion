'use client';
import { useQuery } from '@tanstack/react-query';
import { publicApi } from '@/lib/api/public';

export function usePublicFeatures() {
  return useQuery({ queryKey: ['public', 'features'], queryFn: publicApi.getFeatures });
}
