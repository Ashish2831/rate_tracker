import { LatestRate } from "@/lib/api";
import styles from "./RateTable.module.css";

type SortKey = "rate_value" | "ingestion_ts" | "provider";
type SortDir = "asc" | "desc";

interface Props {
  rates: LatestRate[];
  sortKey: SortKey;
  sortDir: SortDir;
  onSort: (key: SortKey) => void;
}

function SortIndicator({ active, dir }: { active: boolean; dir: SortDir }) {
  if (!active) return <span className={styles.sort}>↕</span>;
  return <span className={styles.sort}>{dir === "asc" ? "↑" : "↓"}</span>;
}

export function RateTable({ rates, sortKey, sortDir, onSort }: Props) {
  if (rates.length === 0) {
    return <p className={styles.empty}>No rates found. Run `make seed` to load data.</p>;
  }

  return (
    <div className={styles.wrapper}>
      <table className={styles.table}>
        <thead>
          <tr>
            <th>
              <button type="button" onClick={() => onSort("provider")}>
                Provider <SortIndicator active={sortKey === "provider"} dir={sortDir} />
              </button>
            </th>
            <th>Rate Type</th>
            <th>
              <button type="button" onClick={() => onSort("rate_value")}>
                Rate (%) <SortIndicator active={sortKey === "rate_value"} dir={sortDir} />
              </button>
            </th>
            <th>
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
              <td>{rate.rate_type.replace(/_/g, " ")}</td>
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
