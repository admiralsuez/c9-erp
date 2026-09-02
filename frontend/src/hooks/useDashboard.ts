import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '../api/analytics';

export const useDashboardOverview = () => {
  return useQuery({
    queryKey: ['dashboard-overview'],
    queryFn: () => analyticsApi.getDashboardOverview(),
    retry: 2,
    refetchInterval: 60_000,
  });
};
