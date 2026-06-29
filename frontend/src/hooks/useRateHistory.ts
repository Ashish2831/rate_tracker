/**
 * Rate history via TanStack Query — cached per provider + type, mapped for charting.
 */

import { keepPreviousData, useQuery } from "@tanstack/react-query";

import {
  UseRateHistoryOptions,
  UseRateHistoryResult,
} from "@/interfaces/hooks";
import { getErrorMessage } from "@/lib/errors";
import { toHistoryPoints } from "@/lib/history";
import { ratesApiClient } from "@/lib/api";
import { rateKeys } from "@/lib/queryKeys";

const HISTORY_STALE_MS = 60_000;

export function useRateHistory({
  provider,
  rateType,
  enabled = true,
  client = ratesApiClient,
}: UseRateHistoryOptions): UseRateHistoryResult {
  const query = useQuery({
    queryKey: rateKeys.history(provider, rateType),
    queryFn: async () => {
      const results = await client.fetchAllRateHistory(provider, rateType);
      return toHistoryPoints(results);
    },
    enabled: enabled && Boolean(provider && rateType),
    staleTime: HISTORY_STALE_MS,
    placeholderData: keepPreviousData,
  });

  return {
    history: query.data ?? [],
    loading: query.isPending && !query.isPlaceholderData,
    error: query.error
      ? getErrorMessage(query.error, "Failed to load rate history.")
      : null,
    refresh: async () => {
      await query.refetch();
    },
  };
}
