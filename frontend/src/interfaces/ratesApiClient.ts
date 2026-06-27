import { HistoryResponse, LatestRatesResponse } from "@/interfaces/rates";

/** DIP — hooks depend on this interface, not concrete fetch implementations. */
export interface RatesApiClient {
  fetchLatestRates(type?: string): Promise<LatestRatesResponse>;
  fetchRateHistory(
    provider: string,
    type: string,
    from?: string,
    to?: string
  ): Promise<HistoryResponse>;
}
