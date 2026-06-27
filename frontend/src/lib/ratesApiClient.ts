import { RatesApiClient } from "@/interfaces/ratesApiClient";
import { fetchLatestRates, fetchRateHistory } from "@/lib/api";

export const ratesApiClient: RatesApiClient = {
  fetchLatestRates,
  fetchRateHistory,
};
