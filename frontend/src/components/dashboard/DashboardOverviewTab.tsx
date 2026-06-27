/** Dashboard overview tab — per-provider cards with best rate and product count. */

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { TabPanel } from "@/components/dashboard/TabPanel";
import { getDashboardTab } from "@/constants/dashboardTabs";
import { LatestRate } from "@/interfaces/rates";
import { formatRateValue } from "@/lib/format";
import { bestRateFromRates } from "@/lib/rates";
import styles from "@/app/page.module.css";

interface Props {
  active: boolean;
  loading: boolean;
  providers: string[];
  providerFilter: string;
  ratesByProvider: Map<string, LatestRate[]>;
}

export function DashboardOverviewTab({
  active,
  loading,
  providers,
  providerFilter,
  ratesByProvider,
}: Props) {
  const tab = getDashboardTab("dashboard");
  const visibleProviders = providers.filter((p) => !providerFilter || p === providerFilter);
  const hasRates = [...ratesByProvider.values()].some((rates) => rates.length > 0);

  return (
    <TabPanel tabId="dashboard" active={active} title={tab.title} description={tab.description}>
      {loading ? (
        <LoadingState message="Loading dashboard..." />
      ) : !hasRates ? (
        <EmptyState
          icon="table"
          title="No rates yet"
          description={
            <>
              Load seed data to get started — run <code>make seed</code> in your terminal.
            </>
          }
        />
      ) : (
        <div className={styles.providerGrid}>
          {visibleProviders.map((provider) => {
            const providerRates = ratesByProvider.get(provider) ?? [];
            const providerBest = bestRateFromRates(providerRates);

            return (
              <div key={provider} className={styles.providerCard}>
                <p className={styles.providerCardName}>{provider}</p>
                <p className={styles.providerCardMeta}>
                  {providerRates.length} product
                  {providerRates.length === 1 ? "" : "s"}
                </p>
                <p className={styles.providerCardRate}>
                  {providerBest !== null ? formatRateValue(providerBest) : "—"}
                </p>
                <p className={styles.providerCardLabel}>Best rate</p>
              </div>
            );
          })}
        </div>
      )}
    </TabPanel>
  );
}
