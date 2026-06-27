/** Unit tests for rate display formatting. */

import { describe, expect, it } from "vitest";

import { formatRateType, formatRateValue } from "@/lib/format";

describe("formatRateType", () => {
  it("title-cases words and uppercases acronyms", () => {
    expect(formatRateType("30yr_fixed_mortgage")).toBe("30yr Fixed Mortgage");
    expect(formatRateType("savings_easy_access")).toBe("Savings Easy Access");
  });
});

describe("formatRateValue", () => {
  it("formats numeric values as percentages", () => {
    expect(formatRateValue(6.5)).toBe("6.50%");
  });

  it("returns em dash for null", () => {
    expect(formatRateValue(null)).toBe("—");
  });
});
