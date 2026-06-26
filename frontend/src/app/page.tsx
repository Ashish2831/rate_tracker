"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ApiError,
  LatestRate,
  RATE_TYPES,
  fetchLatestRates,
  fetchRateHistory,
} from "@/lib/api";
import { RateChart } from "@/components/RateChart";
import { RateTable } from "@/components/RateTable";
import { ErrorBanner } from "@/components/ErrorBanner";
import { LoadingState } from "@/components/LoadingState";
import styles from "./page.module.css";

const REFRESH_INTERVAL_MS = 60_000;

type SortKey = "rate_value" | "ingestion_ts" | "provider";
type SortDir = "asc" | "desc";

export default function DashboardPage() {
  const [rates, setRates] = useState<LatestRate[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<string>("");
  const [selectedType, setSelectedType] = useState<string>(RATE_TYPES[0]);
  const [history, setHistory] = useState<{ effective_date: string; rate_value: number }[]>([]);
  const [sortKey, setSortKey] = useState<SortKey>("rate_value");
  const [sortDir, setSortDir] = useState<SortDir>("asc");
  const [typeFilter, setTypeFilter] = useState<string>("");
  const [latestLoading, setLatestLoading] = useState(true);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [latestError, setLatestError] = useState<string | null>(null);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const loadLatest = useCallback(async () => {
    setLatestLoading(true);
    setLatestError(null);
    try {
      const data = await fetchLatestRates(typeFilter || undefined);
      setRates(data.results);
      setLastUpdated(new Date());
      if (!selectedProvider && data.results.length > 0) {
        setSelectedProvider(data.results[0].provider);
      }
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Failed to load latest rates.";
      setLatestError(message);
    } finally {
      setLatestLoading(false);
    }
  }, [typeFilter, selectedProvider]);

  const loadHistory = useCallback(async () => {
    if (!selectedProvider || !selectedType) return;
    setHistoryLoading(true);
    setHistoryError(null);
    try {
      const data = await fetchRateHistory(selectedProvider, selectedType);
      setHistory(
        data.results
          .filter((r) => r.rate_value !== null)
          .map((r) => ({
            effective_date: r.effective_date,
            rate_value: Number(r.rate_value),
          }))
      );
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Failed to load rate history.";
      setHistoryError(message);
      setHistory([]);
    } finally {
      setHistoryLoading(false);
    }
  }, [selectedProvider, selectedType]);

  useEffect(() => {
    loadLatest();
    const interval = setInterval(loadLatest, REFRESH_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [loadLatest]);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  const sortedRates = useMemo(() => {
    const copy = [...rates];
    copy.sort((a, b) => {
      let aVal: string | number = a[sortKey] as string | number;
      let bVal: string | number = b[sortKey] as string | number;
      if (sortKey === "rate_value") {
        aVal = Number(a.rate_value ?? 0);
        bVal = Number(b.rate_value ?? 0);
      }
      if (aVal < bVal) return sortDir === "asc" ? -1 : 1;
      if (aVal > bVal) return sortDir === "asc" ? 1 : -1;
      return 0;
    });
    return copy;
  }, [rates, sortKey, sortDir]);

  const providers = useMemo(
    () => Array.from(new Set(rates.map((r) => r.provider))).sort(),
    [rates]
  );

  function toggleSort(key: SortKey) {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
  }

  return (
    <main className={styles.main}>
      <header className={styles.header}>
        <div>
          <h1>Rate Tracker</h1>
          <p className={styles.subtitle}>Live interest rate comparison dashboard</p>
        </div>
        {lastUpdated && (
          <p className={styles.meta}>Last refreshed: {lastUpdated.toLocaleTimeString()}</p>
        )}
      </header>

      <section className={styles.filters}>
        <label>
          Filter by type
          <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}>
            <option value="">All types</option>
            {RATE_TYPES.map((t) => (
              <option key={t} value={t}>
                {t.replace(/_/g, " ")}
              </option>
            ))}
          </select>
        </label>
      </section>

      {latestError && <ErrorBanner message={latestError} onRetry={loadLatest} />}

      <section className={styles.card}>
        <h2>Latest Rates by Provider</h2>
        {latestLoading ? (
          <LoadingState message="Loading latest rates..." />
        ) : (
          <RateTable rates={sortedRates} sortKey={sortKey} sortDir={sortDir} onSort={toggleSort} />
        )}
      </section>

      <section className={styles.card}>
        <h2>30-Day Rate History</h2>
        <div className={styles.chartControls}>
          <label>
            Provider
            <select value={selectedProvider} onChange={(e) => setSelectedProvider(e.target.value)}>
              {providers.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
          </label>
          <label>
            Rate type
            <select value={selectedType} onChange={(e) => setSelectedType(e.target.value)}>
              {RATE_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t.replace(/_/g, " ")}
                </option>
              ))}
            </select>
          </label>
        </div>
        {historyError && <ErrorBanner message={historyError} onRetry={loadHistory} />}
        {historyLoading ? (
          <LoadingState message="Loading history chart..." />
        ) : (
          <RateChart data={history} provider={selectedProvider} rateType={selectedType} />
        )}
      </section>
    </main>
  );
}
