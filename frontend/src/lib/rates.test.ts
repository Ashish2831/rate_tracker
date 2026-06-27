/** Unit tests for rate aggregation and grouping helpers. */

import { describe, expect, it } from "vitest";

import { LatestRate } from "@/interfaces/rates";
import { bestRateFromRates, groupRatesByProvider } from "@/lib/rates";

const sample: LatestRate[] = [
  {
    provider: "Chase",
    rate_type: "30yr_fixed_mortgage",
    rate_value: "6.50",
    effective_date: "2025-05-20",
    ingestion_ts: "2025-05-20T10:00:00Z",
    currency: "USD",
  },
  {
    provider: "Chase",
    rate_type: "savings_1yr_fixed",
    rate_value: "4.00",
    effective_date: "2025-05-26",
    ingestion_ts: "2025-05-26T10:00:00Z",
    currency: "USD",
  },
  {
    provider: "HSBC",
    rate_type: "30yr_fixed_mortgage",
    rate_value: "6.75",
    effective_date: "2025-05-15",
    ingestion_ts: "2025-05-15T10:00:00Z",
    currency: "USD",
  },
];

describe("groupRatesByProvider", () => {
  it("groups rates under each provider name", () => {
    const grouped = groupRatesByProvider(sample);
    expect(grouped.get("Chase")).toHaveLength(2);
    expect(grouped.get("HSBC")).toHaveLength(1);
  });
});

describe("bestRateFromRates", () => {
  it("returns the highest numeric rate", () => {
    expect(bestRateFromRates(sample)).toBe(6.75);
  });

  it("returns null when no valid rates exist", () => {
    expect(
      bestRateFromRates([
        {
          ...sample[0],
          rate_value: null,
        },
      ]),
    ).toBeNull();
  });
});
