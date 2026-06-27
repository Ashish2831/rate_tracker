/**
 * Fetches latest rates with 60s auto-refresh.
 * Accepts injectable RatesApiClient for testing (DIP).
 * Shows loading spinner only on initial load / filter change — not on background polls.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

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
  const hasLoadedRef = useRef(false);

  // Re-show loading when the user changes the type filter.
  useEffect(() => {
    hasLoadedRef.current = false;
  }, [typeFilter]);

  const refresh = useCallback(async () => {
    setError(null);
    if (!hasLoadedRef.current) {
      setLoading(true);
    }
    try {
      const { results } = await client.fetchLatestRates(typeFilter || undefined);
      setRates(results);
      setLastUpdated(new Date());
      hasLoadedRef.current = true;
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
