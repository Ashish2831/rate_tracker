/** Injectable API surface for hooks (Dependency Inversion). */

import { HistoryResponse, LatestRatesResponse } from "@/interfaces/rates";

export interface RatesApiClient {
  fetchLatestRates(type?: string): Promise<LatestRatesResponse>;
  fetchRateHistory(
    provider: string,
    type: string,
    from?: string,
    to?: string
  ): Promise<HistoryResponse>;
}
