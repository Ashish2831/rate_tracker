/**
 * Backend API client — fetch helpers and injectable RatesApiClient (DIP).
 * Uses cache: "no-store" so auto-refresh always gets fresh data.
 */

import { HistoryRate, LatestRatesResponse, RateFiltersResponse } from "@/interfaces/rates";
import { RatesApiClient } from "@/interfaces/ratesApiClient";

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

function nextHistoryPath(next: string): string {
  if (!next.startsWith("http")) {
    return next;
  }
  const { pathname, search } = new URL(next);
  if (API_URL.startsWith("http")) {
    return next;
  }
  const apiPrefix = API_URL.startsWith("/") ? API_URL : `/${API_URL}`;
  if (pathname.startsWith(apiPrefix)) {
    return `${pathname.slice(apiPrefix.length)}${search}`;
  }
  return `${pathname}${search}`;
}

interface PaginatedResponse<T> {
  results: T[];
  next: string | null;
}

async function fetchAllPages<T>(firstPath: string): Promise<T[]> {
  const results: T[] = [];
  let path: string | null = firstPath;

  while (path !== null) {
    const currentPath: string = path;
    const page = await fetchJson<PaginatedResponse<T>>(currentPath);
    results.push(...page.results);
    path = page.next ? nextHistoryPath(page.next) : null;
  }

  return results;
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

/** Fetch every page of history for charting (seed data has many snapshots per day). */
async function fetchAllRateHistory(
  provider: string,
  type: string,
  from?: string,
  to?: string
): Promise<HistoryRate[]> {
  const params = new URLSearchParams({ provider, type, page_size: "200" });
  if (from) params.set("from", from);
  if (to) params.set("to", to);

  return fetchAllPages<HistoryRate>(`/rates/history?${params.toString()}`);
}

function buildIngestedParams(
  provider?: string,
  type?: string,
  from?: string,
  to?: string
): URLSearchParams {
  const params = new URLSearchParams({ page_size: "200" });
  if (provider) params.set("provider", provider);
  if (type) params.set("type", type);
  if (from) params.set("from", from);
  if (to) params.set("to", to);
  return params;
}

/** Fetch every page of ingested rates for the 24-hour table. */
async function fetchAllIngestedRates(
  provider?: string,
  type?: string,
  from?: string,
  to?: string
): Promise<HistoryRate[]> {
  const params = buildIngestedParams(provider, type, from, to);
  return fetchAllPages<HistoryRate>(`/rates/ingested?${params.toString()}`);
}

/** Default client injected into hooks; swap in tests. */
export const ratesApiClient: RatesApiClient = {
  fetchLatestRates,
  fetchRateFilters,
  fetchAllRateHistory,
  fetchAllIngestedRates,
};
