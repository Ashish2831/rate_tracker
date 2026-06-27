/**
 * Fetches latest rates with 60s auto-refresh.
 * Accepts injectable RatesApiClient for testing (DIP).
 */

import { useCallback, useEffect, useMemo, useState } from "react";

import { UseLatestRatesOptions, UseLatestRatesResult } from "@/interfaces/hooks";
import { LatestRate } from "@/interfaces/rates";
import { getErrorMessage } from "@/lib/errors";
import { ratesApiClient } from "@/lib/api";
import { uniqueProviders, uniqueRateTypes } from "@/lib/rates";

const DEFAULT_REFRESH_MS = 60_000;

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
      const { results } = await client.fetchLatestRates(typeFilter || undefined);
      setRates(results);
      setLastUpdated(new Date());
    } catch (err) {
      setError(getErrorMessage(err, "Failed to load latest rates."));
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
    providers: useMemo(() => uniqueProviders(rates), [rates]),
    rateTypes: useMemo(() => uniqueRateTypes(rates), [rates]),
    loading,
    error,
    lastUpdated,
    refresh,
  };
}
