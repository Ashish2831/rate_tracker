/** Derived helpers for dashboard display. */

import { LatestRate } from "@/interfaces/rates";

/** Group latest rates by provider for the dashboard overview cards. */
export function groupRatesByProvider(rates: LatestRate[]): Map<string, LatestRate[]> {
  const grouped = new Map<string, LatestRate[]>();
  for (const rate of rates) {
    const existing = grouped.get(rate.provider) ?? [];
    existing.push(rate);
    grouped.set(rate.provider, existing);
  }
  return grouped;
}
