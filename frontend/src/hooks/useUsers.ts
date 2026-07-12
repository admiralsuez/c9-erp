import { useQuery } from '@tanstack/react-query';
import { usersApi } from '../api/users';

/**
 * Fetch users for name resolution. The list endpoint is admin-only,
 * so failures (403) are tolerated silently — callers should fall back
 * to displaying "User #id".
 */
export const useUsers = () => {
  return useQuery({
    queryKey: ['users'],
    queryFn: () => usersApi.list(1, 100),
    retry: false,
    staleTime: 5 * 60 * 1000,
  });
};

/** Build a user_id -> full_name lookup from the users query result. */
export const useUserNameMap = (): Record<number, string> => {
  const { data } = useUsers();
  const map: Record<number, string> = {};
  if (data?.items) {
    for (const user of data.items) {
      map[user.id] = user.full_name;
    }
  }
  return map;
};
