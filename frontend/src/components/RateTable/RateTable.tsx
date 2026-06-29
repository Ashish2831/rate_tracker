/** Sortable comparison table for latest and ingested rates. */

import { ReactNode } from "react";

import { EmptyState } from "@/components/EmptyState";
import { SortableHeader } from "@/components/RateTable/SortableHeader";
import { rateRowKey } from "@/components/RateTable/utils";
import { Rate, SortDir, SortKey } from "@/interfaces/rates";
import { formatRateType, formatRateValue } from "@/lib/format";
import { numericRateValue } from "@/lib/rates";
import styles from "./RateTable.module.css";

interface Props {
  rates: Rate[];
  sortKey: SortKey;
  sortDir: SortDir;
  onSort: (key: SortKey) => void;
  isSorting?: boolean;
  variant?: "latest" | "ingested";
  emptyTitle?: string;
  emptyDescription?: ReactNode;
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
              Load seed data to get started — run <code>make seed</code> in your
              terminal.
            </>
          )
        }
      />
    );
  }

  const showEffectiveDate = variant === "ingested";
  const updatedLabel = showEffectiveDate ? "Ingested At" : "Last Updated";

  return (
    <div className={styles.wrapper} aria-busy={isSorting || undefined}>
      <table className={styles.table}>
        <thead>
          <tr>
            <SortableHeader
              label="Provider"
              columnKey="provider"
              activeKey={sortKey}
              sortDir={sortDir}
              onSort={onSort}
            />
            <th>Rate Type</th>
            <SortableHeader
              label="Rate"
              columnKey="rate_value"
              activeKey={sortKey}
              sortDir={sortDir}
              onSort={onSort}
            />
            {showEffectiveDate && <th>Effective Date</th>}
            <SortableHeader
              label={updatedLabel}
              columnKey="ingestion_ts"
              activeKey={sortKey}
              sortDir={sortDir}
              onSort={onSort}
            />
          </tr>
        </thead>
        <tbody>
          {rates.map((rate, index) => (
            <tr key={rateRowKey(rate, index)}>
              <td>
                <span className={styles.provider}>{rate.provider}</span>
              </td>
              <td>
                <span className={styles.typeBadge}>
                  {formatRateType(rate.rate_type)}
                </span>
              </td>
              <td>
                <span className={styles.rateValue}>
                  {formatRateValue(numericRateValue(rate))}
                </span>
              </td>
              {showEffectiveDate && (
                <td className={styles.timestamp}>{rate.effective_date}</td>
              )}
              <td className={styles.timestamp}>
                {new Date(rate.ingestion_ts).toLocaleString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
