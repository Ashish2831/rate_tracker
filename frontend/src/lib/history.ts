/** History helpers — map API rows to chart points (dbt already dedupes per effective_date). */

import { HistoryPoint, HistoryRate } from "@/interfaces/rates";

/** Map paginated history results to sorted chart points. */
export function toHistoryPoints(results: HistoryRate[]): HistoryPoint[] {
  return results
    .filter((rate) => rate.rate_value !== null)
    .map((rate) => ({
      effective_date: rate.effective_date,
      rate_value: Number(rate.rate_value),
    }))
    .sort((a, b) => a.effective_date.localeCompare(b.effective_date));
}
