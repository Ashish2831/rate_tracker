/** Derived helpers for dashboard display. */

import { LatestRate } from "@/interfaces/rates";

export function numericRateValue(rate: LatestRate): number | null {
  return rate.rate_value !== null ? Number(rate.rate_value) : null;
}

/** Highest numeric rate in a list, or null when no valid values exist. */
export function bestRateFromRates(rates: LatestRate[]): number | null {
  let best: number | null = null;
  for (const rate of rates) {
    const value = numericRateValue(rate);
    if (value !== null && (best === null || value > best)) {
      best = value;
    }
  }
  return best;
}

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
