export interface LatestRate {
  provider: string;
  rate_type: string;
  rate_value: string | number | null;
  effective_date: string;
  ingestion_ts: string;
  currency: string;
}

export interface LatestRatesResponse {
  count: number;
  results: LatestRate[];
  cached: boolean;
}

export interface HistoryRate {
  id: number;
  provider: string;
  rate_type: string;
  rate_value: string | number | null;
  effective_date: string;
  ingestion_ts: string;
  currency: string;
}

export interface HistoryResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: HistoryRate[];
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, { cache: "no-store" });
  if (!response.ok) {
    const body = await response.text();
    throw new ApiError(body || `Request failed with status ${response.status}`, response.status);
  }
  return response.json();
}

export function fetchLatestRates(type?: string): Promise<LatestRatesResponse> {
  const query = type ? `?type=${encodeURIComponent(type)}` : "";
  return fetchJson<LatestRatesResponse>(`/rates/latest${query}`);
}

export function fetchRateHistory(
  provider: string,
  type: string,
  from?: string,
  to?: string
): Promise<HistoryResponse> {
  const params = new URLSearchParams({ provider, type });
  if (from) params.set("from", from);
  if (to) params.set("to", to);
  return fetchJson<HistoryResponse>(`/rates/history?${params.toString()}`);
}

export const RATE_TYPES = [
  "30yr_fixed_mortgage",
  "15yr_fixed_mortgage",
  "5yr_arm_mortgage",
  "savings_easy_access",
  "savings_1yr_fixed",
];
