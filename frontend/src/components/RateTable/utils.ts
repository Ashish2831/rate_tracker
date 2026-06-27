/** Accessibility and React key helpers for RateTable rows and columns. */

import { Rate, SortDir, SortKey } from "@/interfaces/rates";

/** Maps sort state to aria-sort for screen readers. */
export function ariaSortValue(
  key: SortKey,
  activeKey: SortKey,
  dir: SortDir,
): "ascending" | "descending" | "none" {
  if (key !== activeKey) return "none";
  return dir === "asc" ? "ascending" : "descending";
}

/** Prefer stable database id for ingested rows; fallback for latest-rate rows without id. */
export function rateRowKey(rate: Rate, index: number): string {
  const withId = rate as Rate & { id?: number };
  if (withId.id != null) {
    return String(withId.id);
  }
  return `${rate.provider}-${rate.rate_type}-${index}`;
}
