import { describe, expect, it } from "vitest";

import { LatestRate } from "@/interfaces/rates";
import { nextSortState, sortRates, uniqueProviders } from "@/lib/sortRates";

const sampleRates: LatestRate[] = [
  {
    provider: "Chase",
    rate_type: "30yr_fixed_mortgage",
    rate_value: "6.75",
    effective_date: "2025-06-01",
    ingestion_ts: "2025-06-01T12:00:00Z",
    currency: "USD",
  },
  {
    provider: "HSBC",
    rate_type: "savings_1yr_fixed",
    rate_value: "4.50",
    effective_date: "2025-06-01",
    ingestion_ts: "2025-06-02T12:00:00Z",
    currency: "USD",
  },
];

describe("sortRates", () => {
  it("sorts by rate_value ascending", () => {
    const sorted = sortRates(sampleRates, "rate_value", "asc");
    expect(sorted[0].provider).toBe("HSBC");
    expect(sorted[1].provider).toBe("Chase");
  });

  it("sorts by provider ascending", () => {
    const sorted = sortRates(sampleRates, "provider", "asc");
    expect(sorted.map((rate) => rate.provider)).toEqual(["Chase", "HSBC"]);
  });
});

describe("nextSortState", () => {
  it("toggles direction when same column clicked", () => {
    expect(nextSortState("rate_value", "asc", "rate_value")).toEqual({
      sortKey: "rate_value",
      sortDir: "desc",
    });
  });

  it("resets to asc when new column clicked", () => {
    expect(nextSortState("rate_value", "desc", "provider")).toEqual({
      sortKey: "provider",
      sortDir: "asc",
    });
  });
});

describe("uniqueProviders", () => {
  it("returns sorted unique provider names", () => {
    expect(uniqueProviders(sampleRates)).toEqual(["Chase", "HSBC"]);
  });
});
