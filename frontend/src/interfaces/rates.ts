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

export interface HistoryPoint {
  effective_date: string;
  rate_value: number;
}
