import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '../api/analytics';

export const useDashboardOverview = (limit?: number) => {
  return useQuery({
    queryKey: ['dashboard-overview', limit],
    queryFn: () => analyticsApi.getDashboardOverview(limit),
    retry: 2,
    refetchInterval: 60_000,
  });
};
