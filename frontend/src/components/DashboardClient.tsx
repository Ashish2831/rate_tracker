/**
 * Client island — interactive dashboard (data fetching, filters, chart).
 */
"use client";

import { DashboardHeader } from "@/components/dashboard/DashboardHeader";
import { DashboardOverviewTab } from "@/components/dashboard/DashboardOverviewTab";
import { DashboardStats } from "@/components/dashboard/DashboardStats";
import { FilterToolbar } from "@/components/dashboard/FilterToolbar";
import { HistoryTab } from "@/components/dashboard/HistoryTab";
import { SortableRatesTab } from "@/components/dashboard/SortableRatesTab";
import { TabBar } from "@/components/dashboard/TabBar";
import { ErrorBanner } from "@/components/ErrorBanner";
import { useDashboard } from "@/hooks/useDashboard";
import styles from "@/app/page.module.css";

export function DashboardClient() {
  const {
    activeTab,
    setActiveTab,
    providerFilter,
    setProviderFilter,
    typeFilter,
    setTypeFilter,
    refreshing,
    handleRefresh,
    retryLatestAndFilters,
    filters,
    latest,
    latestSort,
    historyReady,
    history,
    ingested,
    ingestedSort,
    bestRate,
    ratesByProvider,
  } = useDashboard();

  const showStats = !latest.loading && !filters.loading && latest.rates.length > 0;

  return (
    <main className={styles.main}>
      <DashboardHeader
        lastUpdated={latest.lastUpdated}
        refreshing={refreshing}
        loading={latest.loading}
        onRefresh={() => void handleRefresh()}
      />

      {showStats && (
        <DashboardStats
          providerCount={filters.providers.length}
          rateTypeCount={filters.rateTypes.length}
          bestRate={bestRate}
        />
      )}

      <FilterToolbar
        providers={filters.providers}
        rateTypes={filters.rateTypes}
        providerFilter={providerFilter}
        typeFilter={typeFilter}
        onProviderChange={setProviderFilter}
        onTypeChange={setTypeFilter}
      />

      <TabBar activeTab={activeTab} onTabChange={setActiveTab} />

      {(latest.error || filters.error) && (
        <ErrorBanner
          message={latest.error ?? filters.error ?? ""}
          onRetry={retryLatestAndFilters}
        />
      )}

      <DashboardOverviewTab
        active={activeTab === "dashboard"}
        loading={latest.loading}
        providers={filters.providers}
        providerFilter={providerFilter}
        ratesByProvider={ratesByProvider}
      />

      <SortableRatesTab
        tabId="latest-by-provider"
        active={activeTab === "latest-by-provider"}
        loading={latest.loading}
        rates={latestSort.sortedRates}
        variant="latest"
        sortKey={latestSort.sortKey}
        sortDir={latestSort.sortDir}
        onSort={latestSort.toggleSort}
        isSorting={latestSort.isSorting}
        loadingMessage="Loading latest rates..."
        badgeSuffix="rates"
        emptyTitle="No matching rates"
        emptyDescription="Try clearing the provider or rate type filters."
      />

      <HistoryTab
        active={activeTab === "history"}
        historyReady={historyReady}
        providerFilter={providerFilter}
        typeFilter={typeFilter}
        history={history.history}
        loading={history.loading}
        error={history.error}
        onRetry={() => void history.refresh()}
      />

      <SortableRatesTab
        tabId="ingested"
        active={activeTab === "ingested"}
        loading={ingested.loading}
        rates={ingestedSort.sortedRates}
        variant="ingested"
        sortKey={ingestedSort.sortKey}
        sortDir={ingestedSort.sortDir}
        onSort={ingestedSort.toggleSort}
        isSorting={ingestedSort.isSorting}
        loadingMessage="Loading ingested records..."
        badgeSuffix="records"
        emptyTitle="No records in this ingestion window"
        emptyDescription="No rates were ingested in the 24-hour window for the current filters."
        error={ingested.error}
        onRetry={() => void ingested.refresh()}
      />
    </main>
  );
}
