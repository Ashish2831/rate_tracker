/** TanStack Query key factory — one place for cache identity per filter/query combo. */

export const rateKeys = {
  all: ["rates"] as const,
  filters: () => [...rateKeys.all, "filters"] as const,
  latest: (provider: string, type: string) =>
    [...rateKeys.all, "latest", provider || "all", type || "all"] as const,
  history: (provider: string, type: string) =>
    [...rateKeys.all, "history", provider, type] as const,
  ingested: (provider: string, type: string) =>
    [...rateKeys.all, "ingested", provider || "all", type || "all"] as const,
};
