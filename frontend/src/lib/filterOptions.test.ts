/** Unit tests for searchable filter option helpers. */

import { describe, expect, it } from "vitest";

import { FilterOption } from "@/interfaces/filters";
import { filterOptions, matchesFilterOption, resolveFilterOption } from "@/lib/filterOptions";

const options = [
  { value: "Chase", label: "Chase" },
  { value: "30yr_fixed_mortgage", label: "30yr Fixed Mortgage" },
  { value: "savings_easy_access", label: "Savings Easy Access" },
];

describe("matchesFilterOption", () => {
  it("matches value and label case-insensitively", () => {
    expect(matchesFilterOption("chase", "Chase", "Chase")).toBe(true);
    expect(matchesFilterOption("30yr", "30yr_fixed_mortgage", "30yr Fixed Mortgage")).toBe(true);
    expect(matchesFilterOption("easy", "savings_easy_access", "Savings Easy Access")).toBe(true);
    expect(matchesFilterOption("wells", "Chase", "Chase")).toBe(false);
  });

  it("returns all options when query is empty", () => {
    expect(matchesFilterOption("", "Chase", "Chase")).toBe(true);
    expect(matchesFilterOption("   ", "Chase", "Chase")).toBe(true);
  });
});

describe("filterOptions", () => {
  it("filters by partial match on value or label", () => {
    expect(filterOptions("chase", options)).toEqual([options[0]]);
    expect(filterOptions("fixed", options)).toEqual([options[1]]);
  });
});

describe("resolveFilterOption", () => {
  it("resolves exact label or value matches", () => {
    expect(resolveFilterOption("Chase", options)).toEqual(options[0]);
    expect(resolveFilterOption("30yr_fixed_mortgage", options)).toEqual(options[1]);
    expect(resolveFilterOption("30yr Fixed Mortgage", options)).toEqual(options[1]);
  });

  it("returns null for partial or unknown input", () => {
    expect(resolveFilterOption("30yr", options)).toBeNull();
    expect(resolveFilterOption("unknown", options)).toBeNull();
    expect(resolveFilterOption("", options)).toBeNull();
  });
});
