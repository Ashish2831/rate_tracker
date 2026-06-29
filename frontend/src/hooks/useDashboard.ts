/**
 * Dashboard orchestration — filters, tab-scoped queries, sort state, and coordinated refresh.
 */

import { useMemo, useState } from "react";

import { DashboardTab } from "@/constants/dashboardTabs";
import { useIngestedRates } from "@/hooks/useIngestedRates";
import { useLatestRates } from "@/hooks/useLatestRates";
import { useRateFilters } from "@/hooks/useRateFilters";
import { useRateHistory } from "@/hooks/useRateHistory";
import { useSortableRates } from "@/hooks/useSortableRates";
import { bestRateFromRates, groupRatesByProvider } from "@/lib/rates";

export function useDashboard() {
  const [activeTab, setActiveTab] = useState<DashboardTab>("dashboard");
  const [providerFilter, setProviderFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [refreshing, setRefreshing] = useState(false);

  const filters = useRateFilters();
  const latest = useLatestRates({ providerFilter, typeFilter });
  const latestSort = useSortableRates(latest.rates);

  const historyReady = Boolean(providerFilter && typeFilter);
  const history = useRateHistory({
    provider: providerFilter,
    rateType: typeFilter,
    // Only fetch when the history tab is active and both filters are set.
    enabled: activeTab === "history" && historyReady,
  });

  const ingested = useIngestedRates({
    provider: providerFilter || undefined,
    rateType: typeFilter || undefined,
    // Defer ingested query until the user opens that tab.
    enabled: activeTab === "ingested",
  });
  const ingestedSort = useSortableRates(ingested.records);

  const bestRate = useMemo(
    () => bestRateFromRates(latest.rates),
    [latest.rates],
  );
  const ratesByProvider = useMemo(
    () => groupRatesByProvider(latest.rates),
    [latest.rates],
  );

  async function handleRefresh() {
    setRefreshing(true);
    const tasks: Promise<void>[] = [latest.refresh(), filters.refresh()];
    if (activeTab === "history" && historyReady) {
      tasks.push(history.refresh());
    }
    if (activeTab === "ingested") {
      tasks.push(ingested.refresh());
    }
    await Promise.all(tasks);
    setRefreshing(false);
  }

  function retryLatestAndFilters() {
    void latest.refresh();
    void filters.refresh();
  }

  return {
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
  };
}
