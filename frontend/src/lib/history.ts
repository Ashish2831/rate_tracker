/** History helpers — daily aggregation for chart display. */

import { HistoryPoint, HistoryRate } from "@/interfaces/rates";

/** Collapse multiple snapshots per effective_date to one daily average rate. */
export function aggregateHistoryByDay(results: HistoryRate[]): HistoryPoint[] {
  const daily = new Map<string, { sum: number; count: number }>();

  for (const rate of results) {
    if (rate.rate_value === null) continue;
    const value = Number(rate.rate_value);
    const bucket = daily.get(rate.effective_date) ?? { sum: 0, count: 0 };
    bucket.sum += value;
    bucket.count += 1;
    daily.set(rate.effective_date, bucket);
  }

  return Array.from(daily.entries())
    .map(([effective_date, { sum, count }]) => ({
      effective_date,
      rate_value: sum / count,
    }))
    .sort((a, b) => a.effective_date.localeCompare(b.effective_date));
}
