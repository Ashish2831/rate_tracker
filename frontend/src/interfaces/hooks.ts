import { HistoryPoint, LatestRate } from "@/interfaces/rates";
import { RatesApiClient } from "@/interfaces/ratesApiClient";
import { SortDir, SortKey } from "@/interfaces/sort";

export interface UseLatestRatesOptions {
  typeFilter?: string;
  refreshIntervalMs?: number;
  client?: RatesApiClient;
}

export interface UseLatestRatesResult {
  rates: LatestRate[];
  providers: string[];
  loading: boolean;
  error: string | null;
  lastUpdated: Date | null;
  refresh: () => Promise<void>;
}

export interface UseRateHistoryOptions {
  provider: string;
  rateType: string;
  client?: RatesApiClient;
}

export interface UseRateHistoryResult {
  history: HistoryPoint[];
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

export interface UseSortableRatesResult {
  sortedRates: LatestRate[];
  sortKey: SortKey;
  sortDir: SortDir;
  toggleSort: (key: SortKey) => void;
}
