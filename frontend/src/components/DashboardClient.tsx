/**
 * Client island — interactive dashboard (data fetching, filters, chart).
 */
"use client";

import dynamic from "next/dynamic";
import { useEffect, useMemo, useState } from "react";

import { RateTable } from "@/components/RateTable";
import { ErrorBanner } from "@/components/ErrorBanner";
import { LoadingState } from "@/components/LoadingState";
import { useLatestRates } from "@/hooks/useLatestRates";
import { useRateHistory } from "@/hooks/useRateHistory";
import { useSortableRates } from "@/hooks/useSortableRates";
import { formatRateType } from "@/lib/format";
import styles from "@/app/page.module.css";

const RateChart = dynamic(
  () => import("@/components/RateChart").then((mod) => mod.RateChart),
  {
    ssr: false,
    loading: () => <LoadingState message="Loading chart..." />,
  }
);

function BrandLogo() {
  return (
    <div className={styles.logo} aria-hidden="true">
      <svg viewBox="0 0 24 24" fill="none">
        <path
          d="M3 17 L7 12 L10 14.5 L16 7 L21 11"
          stroke="#fff"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <circle cx="21" cy="11" r="1.5" fill="#99f6e4" />
      </svg>
    </div>
  );
}

export function DashboardClient() {
  const [typeFilter, setTypeFilter] = useState("");
  const [selectedType, setSelectedType] = useState("");
  const [selectedProvider, setSelectedProvider] = useState("");
  const [refreshing, setRefreshing] = useState(false);

  const { rates, providers, rateTypes, loading, error, lastUpdated, refresh } = useLatestRates({
    typeFilter,
  });
  const { sortedRates, sortKey, sortDir, toggleSort, isSorting } = useSortableRates(rates);
  const {
    history,
    loading: historyLoading,
    error: historyError,
    refresh: refreshHistory,
  } = useRateHistory({ provider: selectedProvider, rateType: selectedType });

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

  const bestRate = useMemo(() => {
    const values = rates
      .map((r) => (r.rate_value !== null ? Number(r.rate_value) : null))
      .filter((v): v is number => v !== null);
    return values.length > 0 ? Math.max(...values) : null;
  }, [rates]);

  async function handleRefresh() {
    setRefreshing(true);
    await Promise.all([refresh(), refreshHistory()]);
    setRefreshing(false);
  }

  return (
    <main className={styles.main}>
      <header className={styles.header}>
        <div className={styles.brand}>
          <BrandLogo />
          <div>
            <h1>Rate Tracker</h1>
            <p className={styles.subtitle}>Live interest rate comparison dashboard</p>
          </div>
        </div>
        <div className={styles.headerActions}>
          {lastUpdated && (
            <span className={styles.liveBadge}>
              <span className={styles.liveDot} aria-hidden="true" />
              Updated {lastUpdated.toLocaleTimeString()}
            </span>
          )}
          <button
            type="button"
            className={styles.refreshBtn}
            onClick={handleRefresh}
            disabled={refreshing || loading}
            aria-label="Refresh data"
          >
            ↻ {refreshing ? "Refreshing…" : "Refresh"}
          </button>
        </div>
      </header>

      {!loading && rates.length > 0 && (
        <div className={styles.stats}>
          <div className={styles.statCard}>
            <p className={styles.statLabel}>Providers</p>
            <p className={styles.statValue}>{providers.length}</p>
          </div>
          <div className={styles.statCard}>
            <p className={styles.statLabel}>Rate Types</p>
            <p className={styles.statValue}>{rateTypes.length}</p>
          </div>
          <div className={styles.statCard}>
            <p className={styles.statLabel}>Best Rate</p>
            <p className={`${styles.statValue} ${styles.statValueAccent}`}>
              {bestRate !== null ? `${bestRate.toFixed(2)}%` : "—"}
            </p>
          </div>
        </div>
      )}

      <section className={styles.toolbar} aria-label="Filters">
        <label className={styles.toolbarLabel}>
          Filter by type
          <select
            className={styles.select}
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
          >
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
        <div className={styles.cardHeader}>
          <h2>Latest Rates by Provider</h2>
          {!loading && sortedRates.length > 0 && (
            <span className={styles.cardBadge}>{sortedRates.length} rates</span>
          )}
        </div>
        {loading ? (
          <LoadingState message="Loading latest rates..." />
        ) : (
          <RateTable
            rates={sortedRates}
            sortKey={sortKey}
            sortDir={sortDir}
            onSort={toggleSort}
            isSorting={isSorting}
          />
        )}
      </section>

      <section className={styles.card}>
        <div className={styles.cardHeader}>
          <h2>30-Day Rate History</h2>
          {!historyLoading && history.length > 0 && (
            <span className={styles.cardBadge}>{history.length} data points</span>
          )}
        </div>
        <div className={styles.chartControls}>
          <label>
            Provider
            <select
              className={styles.select}
              value={selectedProvider}
              onChange={(e) => setSelectedProvider(e.target.value)}
            >
              {providers.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
          </label>
          <label>
            Rate type
            <select
              className={styles.select}
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
            >
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
