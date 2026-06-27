/** Pure sort utilities — testable without React (Vitest). */

import { LatestRate, SortDir, SortKey } from "@/interfaces/rates";

function compareValues(aVal: string | number, bVal: string | number, sortDir: SortDir): number {
  if (aVal < bVal) return sortDir === "asc" ? -1 : 1;
  if (aVal > bVal) return sortDir === "asc" ? 1 : -1;
  return 0;
}

function resolveSortValue(rate: LatestRate, sortKey: SortKey): string | number {
  if (sortKey === "rate_value") {
    return Number(rate.rate_value ?? 0);
  }
  return rate[sortKey] as string | number;
}

export function sortRates(rates: LatestRate[], sortKey: SortKey, sortDir: SortDir): LatestRate[] {
  return [...rates].sort((a, b) =>
    compareValues(resolveSortValue(a, sortKey), resolveSortValue(b, sortKey), sortDir)
  );
}

/** Toggle direction when clicking the same column; reset to asc on new column. */
export function nextSortState(
  currentKey: SortKey,
  currentDir: SortDir,
  clickedKey: SortKey
): { sortKey: SortKey; sortDir: SortDir } {
  if (currentKey === clickedKey) {
    return { sortKey: clickedKey, sortDir: currentDir === "asc" ? "desc" : "asc" };
  }
  return { sortKey: clickedKey, sortDir: "asc" };
}
