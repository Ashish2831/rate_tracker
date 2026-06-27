/** Sortable table tab — shared by latest rates and ingested (24h) views. */

/** Shared sortable table tab — used by latest rates and ingested (24h) views. */

import { ReactNode } from "react";

import { ErrorBanner } from "@/components/ErrorBanner";
import { LoadingState } from "@/components/LoadingState";
import { RateTable } from "@/components/RateTable";
import { TabPanel } from "@/components/dashboard/TabPanel";
import { DashboardTab, getDashboardTab } from "@/constants/dashboardTabs";
import { Rate, SortDir, SortKey } from "@/interfaces/rates";
import styles from "@/app/page.module.css";

interface Props {
  tabId: Extract<DashboardTab, "latest-by-provider" | "ingested">;
  active: boolean;
  loading: boolean;
  rates: Rate[];
  variant: "latest" | "ingested";
  sortKey: SortKey;
  sortDir: SortDir;
  onSort: (key: SortKey) => void;
  isSorting?: boolean;
  loadingMessage: string;
  badgeSuffix: string;
  emptyTitle: string;
  emptyDescription: ReactNode;
  error?: string | null;
  onRetry?: () => void;
}

export function SortableRatesTab({
  tabId,
  active,
  loading,
  rates,
  variant,
  sortKey,
  sortDir,
  onSort,
  isSorting,
  loadingMessage,
  badgeSuffix,
  emptyTitle,
  emptyDescription,
  error,
  onRetry,
}: Props) {
  const tab = getDashboardTab(tabId);

  return (
    <TabPanel
      tabId={tabId}
      active={active}
      title={tab.title}
      description={tab.description}
      badge={
        !loading && rates.length > 0 ? (
          <span className={styles.cardBadge}>
            {rates.length} {badgeSuffix}
          </span>
        ) : undefined
      }
    >
      {error && onRetry && <ErrorBanner message={error} onRetry={onRetry} />}
      {loading ? (
        <LoadingState message={loadingMessage} />
      ) : (
        <RateTable
          rates={rates}
          sortKey={sortKey}
          sortDir={sortDir}
          onSort={onSort}
          isSorting={isSorting}
          variant={variant}
          emptyTitle={emptyTitle}
          emptyDescription={emptyDescription}
        />
      )}
    </TabPanel>
  );
}
