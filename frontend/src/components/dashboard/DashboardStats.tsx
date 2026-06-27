/** Summary stat cards — provider count, rate-type count, and best rate across filters. */

import styles from "@/app/page.module.css";

interface Props {
  providerCount: number;
  rateTypeCount: number;
  bestRate: number | null;
}

export function DashboardStats({ providerCount, rateTypeCount, bestRate }: Props) {
  return (
    <div className={styles.stats}>
      <div className={styles.statCard}>
        <p className={styles.statLabel}>Providers</p>
        <p className={styles.statValue}>{providerCount}</p>
      </div>
      <div className={styles.statCard}>
        <p className={styles.statLabel}>Rate Types</p>
        <p className={styles.statValue}>{rateTypeCount}</p>
      </div>
      <div className={styles.statCard}>
        <p className={styles.statLabel}>Best Rate</p>
        <p className={`${styles.statValue} ${styles.statValueAccent}`}>
          {bestRate !== null ? `${bestRate.toFixed(2)}%` : "—"}
        </p>
      </div>
    </div>
  );
}
