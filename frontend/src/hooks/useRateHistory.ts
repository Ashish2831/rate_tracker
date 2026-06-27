import { useCallback, useEffect, useState } from "react";

import { UseRateHistoryOptions, UseRateHistoryResult } from "@/interfaces/hooks";
import { HistoryPoint } from "@/interfaces/rates";
import { RatesApiClient } from "@/interfaces/ratesApiClient";
import { ApiError } from "@/lib/api";
import { ratesApiClient } from "@/lib/ratesApiClient";

function toHistoryPoints(
  results: Awaited<ReturnType<RatesApiClient["fetchRateHistory"]>>["results"]
): HistoryPoint[] {
  return results
    .filter((rate) => rate.rate_value !== null)
    .map((rate) => ({
      effective_date: rate.effective_date,
      rate_value: Number(rate.rate_value),
    }));
}

/** SRP — owns history fetch and loading/error state for the chart. */
export function useRateHistory({
  provider,
  rateType,
  client = ratesApiClient,
}: UseRateHistoryOptions): UseRateHistoryResult {
  const [history, setHistory] = useState<HistoryPoint[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    if (!provider || !rateType) {
      setHistory([]);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const data = await client.fetchRateHistory(provider, rateType);
      setHistory(toHistoryPoints(data.results));
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Failed to load rate history.";
      setError(message);
      setHistory([]);
    } finally {
      setLoading(false);
    }
  }, [client, provider, rateType]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { history, loading, error, refresh };
}
