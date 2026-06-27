/**
 * Backend API client — fetch helpers and injectable RatesApiClient (DIP).
 * Uses cache: "no-store" so auto-refresh always gets fresh data.
 */

import {
  HistoryRate,
  HistoryResponse,
  IngestedRatesResponse,
  LatestRatesResponse,
  RateFiltersResponse,
} from "@/interfaces/rates";
import { RatesApiClient } from "@/interfaces/ratesApiClient";
import { fetchAllPages } from "@/lib/apiPagination";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "/api";

export class ApiError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ApiError";
  }
}

function resolveFetchUrl(pathOrUrl: string): string {
  if (pathOrUrl.startsWith("http")) {
    return pathOrUrl;
  }
  return `${API_URL}${pathOrUrl}`;
}

async function fetchJson<T>(pathOrUrl: string): Promise<T> {
  const response = await fetch(resolveFetchUrl(pathOrUrl), { cache: "no-store" });
  if (!response.ok) {
    const body = await response.text();
    throw new ApiError(body || `Request failed with status ${response.status}`);
  }
  return response.json();
}

function fetchLatestRates(provider?: string, type?: string): Promise<LatestRatesResponse> {
  const params = new URLSearchParams();
  if (provider) params.set("provider", provider);
  if (type) params.set("type", type);
  const query = params.toString();
  return fetchJson<LatestRatesResponse>(`/rates/latest${query ? `?${query}` : ""}`);
}

function fetchRateFilters(): Promise<RateFiltersResponse> {
  return fetchJson<RateFiltersResponse>("/rates/filters");
}

function buildListParams(
  provider?: string,
  type?: string,
  from?: string,
  to?: string,
  requiredProviderType = false,
): URLSearchParams {
  const params = new URLSearchParams({ page_size: "200" });
  if (requiredProviderType && provider && type) {
    params.set("provider", provider);
    params.set("type", type);
  } else {
    if (provider) params.set("provider", provider);
    if (type) params.set("type", type);
  }
  if (from) params.set("from", from);
  if (to) params.set("to", to);
  return params;
}

/** Fetch every page of history for charting (seed data has many snapshots per day). */
async function fetchAllRateHistory(
  provider: string,
  type: string,
  from?: string,
  to?: string,
): Promise<HistoryRate[]> {
  const params = buildListParams(provider, type, from, to, true);
  return fetchAllPages<HistoryRate>(
    `/rates/history?${params.toString()}`,
    (path) => fetchJson<HistoryResponse>(path),
    API_URL,
  );
}

/** Fetch every page of ingested rates for the 24-hour table. */
async function fetchAllIngestedRates(
  provider?: string,
  type?: string,
  from?: string,
  to?: string,
): Promise<HistoryRate[]> {
  const params = buildListParams(provider, type, from, to);
  return fetchAllPages<HistoryRate>(
    `/rates/ingested?${params.toString()}`,
    (path) => fetchJson<IngestedRatesResponse>(path),
    API_URL,
  );
}

/** Default client injected into hooks; swap in tests. */
export const ratesApiClient: RatesApiClient = {
  fetchLatestRates,
  fetchRateFilters,
  fetchAllRateHistory,
  fetchAllIngestedRates,
};
