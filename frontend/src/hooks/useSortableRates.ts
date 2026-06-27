/** Table sort state — useTransition keeps sorting responsive (concurrent rendering). */

import { useCallback, useMemo, useState, useTransition } from "react";

import { UseSortableRatesResult } from "@/interfaces/hooks";
import { LatestRate, SortDir, SortKey } from "@/interfaces/rates";
import { nextSortState, sortRates } from "@/lib/sortRates";

export function useSortableRates(
  rates: LatestRate[],
  initialKey: SortKey = "rate_value",
  initialDir: SortDir = "asc"
): UseSortableRatesResult {
  const [sortKey, setSortKey] = useState<SortKey>(initialKey);
  const [sortDir, setSortDir] = useState<SortDir>(initialDir);
  const [isSorting, startTransition] = useTransition();

  const sortedRates = useMemo(() => sortRates(rates, sortKey, sortDir), [rates, sortKey, sortDir]);

  const toggleSort = useCallback(
    (key: SortKey) => {
      startTransition(() => {
        const next = nextSortState(sortKey, sortDir, key);
        setSortKey(next.sortKey);
        setSortDir(next.sortDir);
      });
    },
    [sortDir, sortKey]
  );

  return { sortedRates, sortKey, sortDir, toggleSort, isSorting };
}
