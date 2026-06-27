import { useCallback, useEffect, useState } from "react";

import { UseLatestRatesOptions, UseLatestRatesResult } from "@/interfaces/hooks";
import { LatestRate } from "@/interfaces/rates";
import { ApiError } from "@/lib/api";
import { ratesApiClient } from "@/lib/ratesApiClient";
import { uniqueProviders } from "@/lib/sortRates";

const DEFAULT_REFRESH_MS = 60_000;

/** SRP — owns latest-rates fetch, auto-refresh, loading/error state. */
export function useLatestRates({
  typeFilter = "",
  refreshIntervalMs = DEFAULT_REFRESH_MS,
  client = ratesApiClient,
}: UseLatestRatesOptions = {}): UseLatestRatesResult {
  const [rates, setRates] = useState<LatestRate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await client.fetchLatestRates(typeFilter || undefined);
      setRates(data.results);
      setLastUpdated(new Date());
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Failed to load latest rates.";
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [client, typeFilter]);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, refreshIntervalMs);
    return () => clearInterval(interval);
  }, [refresh, refreshIntervalMs]);

  return {
    rates,
    providers: uniqueProviders(rates),
    loading,
    error,
    lastUpdated,
    refresh,
  };
}
