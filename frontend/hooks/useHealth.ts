'use client';
import { useQuery } from '@tanstack/react-query';
import { healthApi } from '@/lib/api/health';

export function useHealth() {
  return useQuery({ queryKey: ['health'], queryFn: healthApi.getHealth, staleTime: 10_000 });
}
