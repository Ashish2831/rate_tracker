/** Sortable comparison table for latest rates by provider. */

import { LatestRate, SortDir, SortKey } from "@/interfaces/rates";
import { formatRateType } from "@/lib/format";
import styles from "./RateTable.module.css";

interface Props {
  rates: LatestRate[];
  sortKey: SortKey;
  sortDir: SortDir;
  onSort: (key: SortKey) => void;
  isSorting?: boolean;
}

function ariaSortValue(key: SortKey, activeKey: SortKey, dir: SortDir): "ascending" | "descending" | "none" {
  if (key !== activeKey) return "none";
  return dir === "asc" ? "ascending" : "descending";
}

function SortIndicator({ active, dir }: { active: boolean; dir: SortDir }) {
  if (!active) return <span className={styles.sort} aria-hidden="true">↕</span>;
  return <span className={styles.sort} aria-hidden="true">{dir === "asc" ? "↑" : "↓"}</span>;
}

export function RateTable({ rates, sortKey, sortDir, onSort, isSorting }: Props) {
  if (rates.length === 0) {
    return <p className={styles.empty}>No rates found. Run `make seed` to load data.</p>;
  }

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
                Rate (%) <SortIndicator active={sortKey === "rate_value"} dir={sortDir} />
              </button>
            </th>
            <th aria-sort={ariaSortValue("ingestion_ts", sortKey, sortDir)}>
              <button type="button" onClick={() => onSort("ingestion_ts")}>
                Last Updated <SortIndicator active={sortKey === "ingestion_ts"} dir={sortDir} />
              </button>
            </th>
          </tr>
        </thead>
        <tbody>
          {rates.map((rate) => (
            <tr key={`${rate.provider}-${rate.rate_type}`}>
              <td>{rate.provider}</td>
              <td>{formatRateType(rate.rate_type)}</td>
              <td className={styles.rateValue}>
                {rate.rate_value !== null ? Number(rate.rate_value).toFixed(2) : "—"}
              </td>
              <td>{new Date(rate.ingestion_ts).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
