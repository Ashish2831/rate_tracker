/** Sortable comparison table for latest and ingested rates. */

import { EmptyState } from "@/components/EmptyState";
import { LatestRate, SortDir, SortKey } from "@/interfaces/rates";
import { formatRateType, formatRateValue } from "@/lib/format";
import styles from "./RateTable.module.css";

interface Props {
  rates: LatestRate[];
  sortKey: SortKey;
  sortDir: SortDir;
  onSort: (key: SortKey) => void;
  isSorting?: boolean;
  variant?: "latest" | "ingested";
  emptyTitle?: string;
  emptyDescription?: string;
}

function ariaSortValue(key: SortKey, activeKey: SortKey, dir: SortDir): "ascending" | "descending" | "none" {
  if (key !== activeKey) return "none";
  return dir === "asc" ? "ascending" : "descending";
}

function rowKey(rate: LatestRate, index: number): string {
  const withId = rate as LatestRate & { id?: number };
  if (withId.id != null) {
    return String(withId.id);
  }
  return `${rate.provider}-${rate.rate_type}-${index}`;
}

function SortIndicator({ active, dir }: { active: boolean; dir: SortDir }) {
  if (!active) return <span className={styles.sort} aria-hidden="true">↕</span>;
  return <span className={`${styles.sort} ${styles.sortActive}`} aria-hidden="true">{dir === "asc" ? "↑" : "↓"}</span>;
}

export function RateTable({
  rates,
  sortKey,
  sortDir,
  onSort,
  isSorting,
  variant = "latest",
  emptyTitle = "No rates yet",
  emptyDescription,
}: Props) {
  if (rates.length === 0) {
    return (
      <EmptyState
        icon="table"
        title={emptyTitle}
        description={
          emptyDescription ?? (
            <>
              Load seed data to get started — run <code>make seed</code> in your terminal.
            </>
          )
        }
      />
    );
  }

  const showEffectiveDate = variant === "ingested";

  return (
    <div className={styles.wrapper} aria-busy={isSorting || undefined}>
      <table className={styles.table}>
        <thead>
          <tr>
            <th aria-sort={ariaSortValue("provider", sortKey, sortDir)}>
              <button type="button" onClick={() => onSort("provider")}>
                Provider <SortIndicator active={sortKey === "provider"} dir={sortDir} />
              </button>
            </th>
            <th>Rate Type</th>
            <th aria-sort={ariaSortValue("rate_value", sortKey, sortDir)}>
              <button type="button" onClick={() => onSort("rate_value")}>
                Rate <SortIndicator active={sortKey === "rate_value"} dir={sortDir} />
              </button>
            </th>
            {showEffectiveDate && <th>Effective Date</th>}
            <th aria-sort={ariaSortValue("ingestion_ts", sortKey, sortDir)}>
              <button type="button" onClick={() => onSort("ingestion_ts")}>
                {showEffectiveDate ? "Ingested At" : "Last Updated"}{" "}
                <SortIndicator active={sortKey === "ingestion_ts"} dir={sortDir} />
              </button>
            </th>
          </tr>
        </thead>
        <tbody>
          {rates.map((rate, index) => (
            <tr key={rowKey(rate, index)}>
              <td>
                <span className={styles.provider}>{rate.provider}</span>
              </td>
              <td>
                <span className={styles.typeBadge}>{formatRateType(rate.rate_type)}</span>
              </td>
              <td>
                <span className={styles.rateValue}>{formatRateValue(rate.rate_value !== null ? Number(rate.rate_value) : null)}</span>
              </td>
              {showEffectiveDate && (
                <td className={styles.timestamp}>{rate.effective_date}</td>
              )}
              <td className={styles.timestamp}>{new Date(rate.ingestion_ts).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
