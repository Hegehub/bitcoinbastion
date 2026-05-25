'use client';
import { useQuery } from '@tanstack/react-query';
import { publicApi } from '@/lib/api/public';

export function usePublicRoadmap() {
  return useQuery({ queryKey: ['public', 'roadmap'], queryFn: publicApi.getRoadmap });
}
