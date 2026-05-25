'use client';
import { useQuery } from '@tanstack/react-query';
import { publicApi } from '@/lib/api/public';

export function usePublicStats() {
  return useQuery({ queryKey: ['public', 'stats'], queryFn: publicApi.getStats });
}
