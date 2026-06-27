"use client";

import { useState } from "react";

import { RateChart } from "@/components/RateChart";
import { RateTable } from "@/components/RateTable";
import { ErrorBanner } from "@/components/ErrorBanner";
import { LoadingState } from "@/components/LoadingState";
import { useDefaultProvider } from "@/hooks/useDefaultProvider";
import { useLatestRates } from "@/hooks/useLatestRates";
import { useRateHistory } from "@/hooks/useRateHistory";
import { useSortableRates } from "@/hooks/useSortableRates";
import { RATE_TYPES } from "@/lib/api";
import styles from "./page.module.css";

export default function DashboardPage() {
  const [typeFilter, setTypeFilter] = useState("");
  const [selectedType, setSelectedType] = useState<string>(RATE_TYPES[0]);

  const { rates, providers, loading, error, lastUpdated, refresh } = useLatestRates({ typeFilter });
  const [selectedProvider, setSelectedProvider] = useDefaultProvider(providers);
  const { sortedRates, sortKey, sortDir, toggleSort } = useSortableRates(rates);
  const {
    history,
    loading: historyLoading,
    error: historyError,
    refresh: refreshHistory,
  } = useRateHistory({ provider: selectedProvider, rateType: selectedType });

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
              {RATE_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t.replace(/_/g, " ")}
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
