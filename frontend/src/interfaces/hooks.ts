/** Hook option and result types — keeps components decoupled from hook internals. */

import { HistoryPoint, IngestedRate, LatestRate } from "@/interfaces/rates";
import { RatesApiClient } from "@/interfaces/ratesApiClient";
import { SortDir, SortKey } from "@/interfaces/rates";

export interface UseLatestRatesOptions {
  providerFilter?: string;
  typeFilter?: string;
  refreshIntervalMs?: number;
  client?: RatesApiClient;
}

export interface UseLatestRatesResult {
  rates: LatestRate[];
  loading: boolean;
  error: string | null;
  lastUpdated: Date | null;
  refresh: () => Promise<void>;
}

export interface UseRateHistoryOptions {
  provider: string;
  rateType: string;
  enabled?: boolean;
  client?: RatesApiClient;
}

export interface UseRateHistoryResult {
  history: HistoryPoint[];
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

export interface UseIngestedRatesOptions {
  provider?: string;
  rateType?: string;
  enabled?: boolean;
  client?: RatesApiClient;
}

export interface UseIngestedRatesResult {
  records: IngestedRate[];
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

export interface UseSortableRatesResult {
  sortedRates: LatestRate[];
  sortKey: SortKey;
  sortDir: SortDir;
  toggleSort: (key: SortKey) => void;
  isSorting?: boolean;
}

export interface UseRateFiltersResult {
  providers: string[];
  rateTypes: string[];
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}
