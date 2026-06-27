/** Derived lists from latest rates for filter/chart dropdowns. */

import { FALLBACK_RATE_TYPES, LatestRate } from "@/interfaces/rates";

export function uniqueProviders(rates: LatestRate[]): string[] {
  return Array.from(new Set(rates.map((rate) => rate.provider))).sort();
}

export function uniqueRateTypes(rates: LatestRate[]): string[] {
  const fromData = Array.from(new Set(rates.map((rate) => rate.rate_type))).sort();
  // Show sensible defaults before seed data is loaded.
  return fromData.length > 0 ? fromData : [...FALLBACK_RATE_TYPES];
}
