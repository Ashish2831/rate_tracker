/** Injectable API surface for hooks (Dependency Inversion — swap in tests). */

import { HistoryRate, LatestRatesResponse, RateFiltersResponse } from "@/interfaces/rates";

export interface RatesApiClient {
  fetchLatestRates(provider?: string, type?: string): Promise<LatestRatesResponse>;
  fetchRateFilters(): Promise<RateFiltersResponse>;
  fetchAllRateHistory(
    provider: string,
    type: string,
    from?: string,
    to?: string
  ): Promise<HistoryRate[]>;
  fetchAllIngestedRates(
    provider?: string,
    type?: string,
    from?: string,
    to?: string
  ): Promise<HistoryRate[]>;
}
