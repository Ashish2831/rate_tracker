/** 30-day history tab — lazy-loads Plotly chart when provider + type are selected. */

import dynamic from "next/dynamic";

import { EmptyState } from "@/components/EmptyState";
import { ErrorBanner } from "@/components/ErrorBanner";
import { LoadingState } from "@/components/LoadingState";
import { TabPanel } from "@/components/dashboard/TabPanel";
import { getDashboardTab } from "@/constants/dashboardTabs";
import { HistoryPoint } from "@/interfaces/rates";
import styles from "@/app/page.module.css";

const RateChart = dynamic(
  () => import("@/components/RateChart").then((mod) => mod.RateChart),
  {
    ssr: false,
    loading: () => <LoadingState message="Loading chart..." />,
  },
);

interface Props {
  active: boolean;
  historyReady: boolean;
  providerFilter: string;
  typeFilter: string;
  history: HistoryPoint[];
  loading: boolean;
  error: string | null;
  onRetry: () => void;
}

export function HistoryTab({
  active,
  historyReady,
  providerFilter,
  typeFilter,
  history,
  loading,
  error,
  onRetry,
}: Props) {
  const tab = getDashboardTab("history");

  return (
    <TabPanel
      tabId="history"
      active={active}
      title={tab.title}
      description={tab.description}
      badge={
        !loading && history.length > 0 ? (
          <span className={styles.cardBadge}>{history.length} data points</span>
        ) : undefined
      }
    >
      {!historyReady ? (
        <EmptyState
          icon="chart"
          title="Select a provider and rate type"
          description="Choose both filters above to view the 30-day rate history chart."
        />
      ) : error ? (
        <ErrorBanner message={error} onRetry={onRetry} />
      ) : loading ? (
        <LoadingState message="Loading history chart..." />
      ) : (
        <RateChart data={history} provider={providerFilter} rateType={typeFilter} />
      )}
    </TabPanel>
  );
}
