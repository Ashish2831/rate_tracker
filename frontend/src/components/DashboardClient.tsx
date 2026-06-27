/**
 * Client island — interactive dashboard (data fetching, filters, chart).
 */
"use client";

import dynamic from "next/dynamic";
import { useMemo, useState } from "react";

import { RateTable } from "@/components/RateTable";
import { ErrorBanner } from "@/components/ErrorBanner";
import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { useIngestedRates } from "@/hooks/useIngestedRates";
import { useLatestRates } from "@/hooks/useLatestRates";
import { useRateFilters } from "@/hooks/useRateFilters";
import { useRateHistory } from "@/hooks/useRateHistory";
import { useSortableRates } from "@/hooks/useSortableRates";
import { formatRateType, formatRateValue } from "@/lib/format";
import { groupRatesByProvider } from "@/lib/rates";
import styles from "@/app/page.module.css";

const RateChart = dynamic(
  () => import("@/components/RateChart").then((mod) => mod.RateChart),
  {
    ssr: false,
    loading: () => <LoadingState message="Loading chart..." />,
  },
);

type DashboardTab = "dashboard" | "latest-by-provider" | "history" | "ingested";

const TABS: { id: DashboardTab; label: string; description: string }[] = [
  {
    id: "dashboard",
    label: "Dashboard",
    description: "Latest rate per provider — summary cards with best rate and product count",
  },
  {
    id: "latest-by-provider",
    label: "Latest Rate By Provider",
    description: "Full comparison table of latest rates grouped by provider and product type",
  },
  {
    id: "history",
    label: "30-Day History",
    description: "Rate change over the last 30 days for a selected provider and type",
  },
  {
    id: "ingested",
    label: "Ingested (24h)",
    description: "Records ingested in the 24-hour window ending at the latest ingestion batch",
  },
];

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
  const [activeTab, setActiveTab] = useState<DashboardTab>("dashboard");
  const [providerFilter, setProviderFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [refreshing, setRefreshing] = useState(false);

  const {
    providers,
    rateTypes,
    loading: filtersLoading,
    error: filtersError,
    refresh: refreshFilters,
  } = useRateFilters();
  const { rates, loading, error, lastUpdated, refresh } = useLatestRates({
    providerFilter,
    typeFilter,
  });

  const { sortedRates, sortKey, sortDir, toggleSort, isSorting } =
    useSortableRates(rates);

  const historyReady = Boolean(providerFilter && typeFilter);

  const {
    history,
    loading: historyLoading,
    error: historyError,
    refresh: refreshHistory,
  } = useRateHistory({
    provider: providerFilter,
    rateType: typeFilter,
    enabled: activeTab === "history" && historyReady,
  });

  const {
    records: ingestedRecords,
    loading: ingestedLoading,
    error: ingestedError,
    refresh: refreshIngested,
  } = useIngestedRates({
    provider: providerFilter || undefined,
    rateType: typeFilter || undefined,
    enabled: activeTab === "ingested",
  });
  const {
    sortedRates: sortedIngested,
    sortKey: ingestedSortKey,
    sortDir: ingestedSortDir,
    toggleSort: toggleIngestedSort,
    isSorting: ingestedSorting,
  } = useSortableRates(ingestedRecords);

  const bestRate = useMemo(() => {
    const values = rates
      .map((r) => (r.rate_value !== null ? Number(r.rate_value) : null))
      .filter((v): v is number => v !== null);
    return values.length > 0 ? Math.max(...values) : null;
  }, [rates]);

  const ratesByProvider = useMemo(() => groupRatesByProvider(rates), [rates]);

  async function handleRefresh() {
    setRefreshing(true);
    const tasks: Promise<void>[] = [refresh(), refreshFilters()];
    if (activeTab === "history" && historyReady) {
      tasks.push(refreshHistory());
    }
    if (activeTab === "ingested") {
      tasks.push(refreshIngested());
    }
    await Promise.all(tasks);
    setRefreshing(false);
  }

  return (
    <main className={styles.main}>
      <header className={styles.header}>
        <div className={styles.brand}>
          <BrandLogo />
          <div>
            <h1>Rate Tracker</h1>
            <p className={styles.subtitle}>
              Live interest rate comparison dashboard
            </p>
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

      {!loading && !filtersLoading && rates.length > 0 && (
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
          Provider
          <select
            className={styles.select}
            value={providerFilter}
            onChange={(e) => setProviderFilter(e.target.value)}
          >
            <option value="">All providers</option>
            {providers.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </label>
        <label className={styles.toolbarLabel}>
          Rate type
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

      <div className={styles.tabs} role="tablist" aria-label="Dashboard views">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            role="tab"
            id={`tab-${tab.id}`}
            aria-selected={activeTab === tab.id}
            aria-controls={`panel-${tab.id}`}
            className={activeTab === tab.id ? styles.tabActive : styles.tab}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {(error || filtersError) && (
        <ErrorBanner
          message={error ?? filtersError ?? ""}
          onRetry={() => {
            void refresh();
            void refreshFilters();
          }}
        />
      )}

      {activeTab === "dashboard" && (
        <section
          className={styles.card}
          role="tabpanel"
          id="panel-dashboard"
          aria-labelledby="tab-dashboard"
        >
          <div className={styles.cardHeader}>
            <div>
              <h2>Dashboard Overview</h2>
              <p className={styles.cardDescription}>{TABS[0].description}</p>
            </div>
          </div>
          {loading ? (
            <LoadingState message="Loading dashboard..." />
          ) : rates.length === 0 ? (
            <EmptyState
              icon="table"
              title="No rates yet"
              description={
                <>
                  Load seed data to get started — run <code>make seed</code> in your
                  terminal.
                </>
              }
            />
          ) : (
            <div className={styles.providerGrid}>
              {providers
                .filter((p) => !providerFilter || p === providerFilter)
                .map((provider) => {
                  const providerRates = ratesByProvider.get(provider) ?? [];
                  const values = providerRates
                    .map((r) =>
                      r.rate_value !== null ? Number(r.rate_value) : null,
                    )
                    .filter((v): v is number => v !== null);
                  const best =
                    values.length > 0 ? Math.max(...values) : null;

                  return (
                    <div key={provider} className={styles.providerCard}>
                      <p className={styles.providerCardName}>{provider}</p>
                      <p className={styles.providerCardMeta}>
                        {providerRates.length} product
                        {providerRates.length === 1 ? "" : "s"}
                      </p>
                      <p className={styles.providerCardRate}>
                        {best !== null ? formatRateValue(best) : "—"}
                      </p>
                      <p className={styles.providerCardLabel}>Best rate</p>
                    </div>
                  );
                })}
            </div>
          )}
        </section>
      )}

      {activeTab === "latest-by-provider" && (
        <section
          className={styles.card}
          role="tabpanel"
          id="panel-latest-by-provider"
          aria-labelledby="tab-latest-by-provider"
        >
          <div className={styles.cardHeader}>
            <div>
              <h2>Latest Rate By Provider</h2>
              <p className={styles.cardDescription}>{TABS[1].description}</p>
            </div>
            {!loading && sortedRates.length > 0 && (
              <span className={styles.cardBadge}>
                {sortedRates.length} rates
              </span>
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
              variant="latest"
              emptyTitle="No matching rates"
              emptyDescription="Try clearing the provider or rate type filters."
            />
          )}
        </section>
      )}

      {activeTab === "history" && (
        <section
          className={styles.card}
          role="tabpanel"
          id="panel-history"
          aria-labelledby="tab-history"
        >
          <div className={styles.cardHeader}>
            <div>
              <h2>30-Day Rate History</h2>
              <p className={styles.cardDescription}>{TABS[2].description}</p>
            </div>
            {!historyLoading && history.length > 0 && (
              <span className={styles.cardBadge}>
                {history.length} data points
              </span>
            )}
          </div>
          {!historyReady ? (
            <EmptyState
              icon="chart"
              title="Select a provider and rate type"
              description="Choose both filters above to view the 30-day rate history chart."
            />
          ) : historyError ? (
            <ErrorBanner message={historyError} onRetry={refreshHistory} />
          ) : historyLoading ? (
            <LoadingState message="Loading history chart..." />
          ) : (
            <RateChart
              data={history}
              provider={providerFilter}
              rateType={typeFilter}
            />
          )}
        </section>
      )}

      {activeTab === "ingested" && (
        <section
          className={styles.card}
          role="tabpanel"
          id="panel-ingested"
          aria-labelledby="tab-ingested"
        >
          <div className={styles.cardHeader}>
            <div>
              <h2>Ingested in Last 24 Hours</h2>
              <p className={styles.cardDescription}>{TABS[3].description}</p>
            </div>
            {!ingestedLoading && sortedIngested.length > 0 && (
              <span className={styles.cardBadge}>
                {sortedIngested.length} records
              </span>
            )}
          </div>
          {ingestedError && (
            <ErrorBanner message={ingestedError} onRetry={refreshIngested} />
          )}
          {ingestedLoading ? (
            <LoadingState message="Loading ingested records..." />
          ) : (
            <RateTable
              rates={sortedIngested}
              sortKey={ingestedSortKey}
              sortDir={ingestedSortDir}
              onSort={toggleIngestedSort}
              isSorting={ingestedSorting}
              variant="ingested"
              emptyTitle="No records in this ingestion window"
              emptyDescription="No rates were ingested in the 24-hour window for the current filters."
            />
          )}
        </section>
      )}
    </main>
  );
}
