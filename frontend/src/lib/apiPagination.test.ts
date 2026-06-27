/** Unit tests for client-side API pagination helpers. */

import { describe, expect, it, vi } from "vitest";

import { fetchAllPages, resolveNextPagePath } from "@/lib/apiPagination";

describe("resolveNextPagePath", () => {
  it("returns relative paths unchanged", () => {
    expect(resolveNextPagePath("/rates/history?page=2", "/api")).toBe("/rates/history?page=2");
  });

  it("strips the API prefix from absolute next URLs", () => {
    expect(
      resolveNextPagePath("http://localhost:8000/api/rates/history?page=2", "/api"),
    ).toBe("/rates/history?page=2");
  });

  it("preserves absolute URLs when API_URL is absolute", () => {
    const next = "http://backend:8000/api/rates/ingested?page=2";
    expect(resolveNextPagePath(next, "http://backend:8000/api")).toBe(next);
  });
});

describe("fetchAllPages", () => {
  it("merges every page until next is null", async () => {
    const fetchPage = vi
      .fn()
      .mockResolvedValueOnce({
        results: [{ id: 1 }, { id: 2 }],
        next: "http://localhost:8000/api/rates/history?page=2",
      })
      .mockResolvedValueOnce({
        results: [{ id: 3 }],
        next: null,
      });

    const results = await fetchAllPages("/rates/history?page=1", fetchPage, "/api");

    expect(results).toEqual([{ id: 1 }, { id: 2 }, { id: 3 }]);
    expect(fetchPage).toHaveBeenCalledTimes(2);
    expect(fetchPage).toHaveBeenNthCalledWith(1, "/rates/history?page=1");
    expect(fetchPage).toHaveBeenNthCalledWith(2, "/rates/history?page=2");
  });
});
