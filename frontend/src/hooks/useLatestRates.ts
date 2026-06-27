/**
 * Latest rates via TanStack Query — cached per filter combo, background refresh every 60s.
 */

import { keepPreviousData, useQuery } from "@tanstack/react-query";

import { UseLatestRatesOptions, UseLatestRatesResult } from "@/interfaces/hooks";
import { getErrorMessage } from "@/lib/errors";
import { ratesApiClient } from "@/lib/api";
import { rateKeys } from "@/lib/queryKeys";

const DEFAULT_REFRESH_MS = 60_000;

export function useLatestRates({
  providerFilter = "",
  typeFilter = "",
  refreshIntervalMs = DEFAULT_REFRESH_MS,
  client = ratesApiClient,
}: UseLatestRatesOptions = {}): UseLatestRatesResult {
  const query = useQuery({
    queryKey: rateKeys.latest(providerFilter, typeFilter),
    queryFn: async () => {
      const response = await client.fetchLatestRates(
        providerFilter || undefined,
        typeFilter || undefined,
      );
      return response.results;
    },
    staleTime: DEFAULT_REFRESH_MS,
    refetchInterval: refreshIntervalMs,
    placeholderData: keepPreviousData,
  });

  return {
    rates: query.data ?? [],
    loading: query.isPending && !query.isPlaceholderData,
    error: query.error ? getErrorMessage(query.error, "Failed to load latest rates.") : null,
    lastUpdated: query.dataUpdatedAt ? new Date(query.dataUpdatedAt) : null,
    refresh: async () => {
      await query.refetch();
    },
  };
}
