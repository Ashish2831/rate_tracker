/** Dashboard header — title, live timestamp, and manual refresh control. */

import { BrandLogo } from "@/components/dashboard/BrandLogo";
import styles from "@/app/page.module.css";

interface Props {
  lastUpdated: Date | null;
  refreshing: boolean;
  loading: boolean;
  onRefresh: () => void;
}

export function DashboardHeader({ lastUpdated, refreshing, loading, onRefresh }: Props) {
  return (
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
          onClick={onRefresh}
          disabled={refreshing || loading}
          aria-label="Refresh data"
        >
          ↻ {refreshing ? "Refreshing…" : "Refresh"}
        </button>
      </div>
    </header>
  );
}
