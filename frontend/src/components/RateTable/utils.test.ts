/** Unit tests for RateTable accessibility and row-key helpers. */

import { describe, expect, it } from "vitest";

import { HistoryRate, LatestRate } from "@/interfaces/rates";
import { ariaSortValue, rateRowKey } from "@/components/RateTable/utils";

describe("ariaSortValue", () => {
  it("returns none for inactive columns", () => {
    expect(ariaSortValue("provider", "rate_value", "asc")).toBe("none");
  });

  it("returns ascending for active asc column", () => {
    expect(ariaSortValue("rate_value", "rate_value", "asc")).toBe("ascending");
  });
});

describe("rateRowKey", () => {
  const base: LatestRate = {
    provider: "Chase",
    rate_type: "30yr_fixed_mortgage",
    rate_value: "6.50",
    effective_date: "2025-05-20",
    ingestion_ts: "2025-05-20T10:00:00Z",
    currency: "USD",
  };

  it("uses id when present", () => {
    const withId: HistoryRate = { ...base, id: 42 };
    expect(rateRowKey(withId, 0)).toBe("42");
  });

  it("falls back to provider-type-index", () => {
    expect(rateRowKey(base, 3)).toBe("Chase-30yr_fixed_mortgage-3");
  });
});
