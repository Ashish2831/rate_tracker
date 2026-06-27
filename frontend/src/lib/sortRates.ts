import { LatestRate } from "@/interfaces/rates";
import { SortDir, SortKey } from "@/interfaces/sort";

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

/** Pure sort function — SRP: table sorting logic isolated from UI. */
export function sortRates(rates: LatestRate[], sortKey: SortKey, sortDir: SortDir): LatestRate[] {
  return [...rates].sort((a, b) => {
    const aVal = resolveSortValue(a, sortKey);
    const bVal = resolveSortValue(b, sortKey);
    return compareValues(aVal, bVal, sortDir);
  });
}

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

export function uniqueProviders(rates: LatestRate[]): string[] {
  return Array.from(new Set(rates.map((rate) => rate.provider))).sort();
}
