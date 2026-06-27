/**
 * Ingested rates via TanStack Query — cached per filter combo.
 */

import { keepPreviousData, useQuery } from "@tanstack/react-query";

import { UseIngestedRatesOptions, UseIngestedRatesResult } from "@/interfaces/hooks";
import { getErrorMessage } from "@/lib/errors";
import { ratesApiClient } from "@/lib/api";
import { rateKeys } from "@/lib/queryKeys";

const INGESTED_STALE_MS = 60_000;

export function useIngestedRates({
  provider = "",
  rateType = "",
  enabled = true,
  client = ratesApiClient,
}: UseIngestedRatesOptions = {}): UseIngestedRatesResult {
  const query = useQuery({
    queryKey: rateKeys.ingested(provider, rateType),
    queryFn: () =>
      client.fetchAllIngestedRates(provider || undefined, rateType || undefined),
    enabled,
    staleTime: INGESTED_STALE_MS,
    placeholderData: keepPreviousData,
  });

  return {
    records: query.data ?? [],
    loading: query.isPending && !query.isPlaceholderData,
    error: query.error ? getErrorMessage(query.error, "Failed to load ingested rates.") : null,
    refresh: async () => {
      await query.refetch();
    },
  };
}
