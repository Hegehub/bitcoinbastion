'use client';
import { useQuery } from '@tanstack/react-query';
import { publicApi } from '@/lib/api/public';

export function usePublicStatus() {
  return useQuery({ queryKey: ['public', 'status'], queryFn: publicApi.getStatus });
}
