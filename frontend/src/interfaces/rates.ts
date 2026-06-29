/** Shared domain types matching backend API JSON shapes. */

/** Core rate fields returned by all list endpoints. */
export interface Rate {
  provider: string;
  rate_type: string;
  rate_value: string | number | null;
  effective_date: string;
  ingestion_ts: string;
  currency: string;
}

export type LatestRate = Rate;
/** History and ingested rows include a database id for stable React keys. */
export type HistoryRate = Rate & { id: number };

export interface LatestRatesResponse {
  count: number;
  results: LatestRate[];
  cached: boolean;
}

export interface RateFiltersResponse {
  providers: string[];
  rate_types: string[];
}

export interface HistoryResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: HistoryRate[];
}

export type IngestedRate = HistoryRate;

export interface IngestedRatesResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: IngestedRate[];
}

/** Chart-friendly point mapped from a deduped mart_rates row. */
export interface HistoryPoint {
  effective_date: string;
  rate_value: number;
}

export type SortKey = "rate_value" | "ingestion_ts" | "provider";
export type SortDir = "asc" | "desc";

/** Shown in dropdowns before seed data loads. */
export const FALLBACK_RATE_TYPES = [
  "30yr_fixed_mortgage",
  "15yr_fixed_mortgage",
  "5yr_arm_mortgage",
  "savings_easy_access",
  "savings_1yr_fixed",
] as const;
