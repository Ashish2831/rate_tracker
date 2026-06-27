/**
 * Dashboard page — composes hooks and presentational components only.
 * Default provider/type selection happens via useEffect when data loads.
 */
"use client";

import { useEffect, useState } from "react";

import { RateChart } from "@/components/RateChart";
import { RateTable } from "@/components/RateTable";
import { ErrorBanner } from "@/components/ErrorBanner";
import { LoadingState } from "@/components/LoadingState";
import { useLatestRates } from "@/hooks/useLatestRates";
import { useRateHistory } from "@/hooks/useRateHistory";
import { useSortableRates } from "@/hooks/useSortableRates";
import { formatRateType } from "@/lib/format";
import styles from "./page.module.css";

export default function DashboardPage() {
  const [typeFilter, setTypeFilter] = useState("");
  const [selectedType, setSelectedType] = useState("");
  const [selectedProvider, setSelectedProvider] = useState("");

  const { rates, providers, rateTypes, loading, error, lastUpdated, refresh } = useLatestRates({
    typeFilter,
  });
  const { sortedRates, sortKey, sortDir, toggleSort } = useSortableRates(rates);
  const {
    history,
    loading: historyLoading,
    error: historyError,
    refresh: refreshHistory,
  } = useRateHistory({ provider: selectedProvider, rateType: selectedType });

  // Auto-select first provider/type once latest rates load.
  useEffect(() => {
    if (!selectedProvider && providers.length > 0) {
      setSelectedProvider(providers[0]);
    }
  }, [providers, selectedProvider]);

  useEffect(() => {
    if (!selectedType && rateTypes.length > 0) {
      setSelectedType(rateTypes[0]);
    }
  }, [rateTypes, selectedType]);

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
            {rateTypes.map((t) => (
              <option key={t} value={t}>
                {formatRateType(t)}
              </option>
            ))}
          </select>
        </label>
      </section>

      {error && <ErrorBanner message={error} onRetry={refresh} />}

      <section className={styles.card}>
        <h2>Latest Rates by Provider</h2>
        {loading ? (
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
              {rateTypes.map((t) => (
                <option key={t} value={t}>
                  {formatRateType(t)}
                </option>
              ))}
            </select>
          </label>
        </div>
        {historyError && <ErrorBanner message={historyError} onRetry={refreshHistory} />}
        {historyLoading ? (
          <LoadingState message="Loading history chart..." />
        ) : (
          <RateChart data={history} provider={selectedProvider} rateType={selectedType} />
        )}
      </section>
    </main>
  );
}
