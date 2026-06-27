/** Filter dropdown options via TanStack Query — fetched once, cached for 5 minutes. */

import { useQuery } from "@tanstack/react-query";

import { UseRateFiltersResult } from "@/interfaces/hooks";
import { FALLBACK_RATE_TYPES } from "@/interfaces/rates";
import { getErrorMessage } from "@/lib/errors";
import { ratesApiClient } from "@/lib/api";
import { rateKeys } from "@/lib/queryKeys";

const FILTER_STALE_MS = 5 * 60_000;

export function useRateFilters(): UseRateFiltersResult {
  const query = useQuery({
    queryKey: rateKeys.filters(),
    queryFn: () => ratesApiClient.fetchRateFilters(),
    staleTime: FILTER_STALE_MS,
  });

  const providers = query.data?.providers ?? [];
  const rateTypes =
    query.data && query.data.rate_types.length > 0
      ? query.data.rate_types
      : [...FALLBACK_RATE_TYPES];

  return {
    providers,
    rateTypes,
    loading: query.isPending,
    error: query.error ? getErrorMessage(query.error, "Failed to load filter options.") : null,
    refresh: async () => {
      await query.refetch();
    },
  };
}
