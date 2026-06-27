/** Table sort state — delegates comparison logic to pure sortRates(). */

import { useCallback, useMemo, useState } from "react";

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

  const sortedRates = useMemo(() => sortRates(rates, sortKey, sortDir), [rates, sortKey, sortDir]);

  const toggleSort = useCallback(
    (key: SortKey) => {
      const next = nextSortState(sortKey, sortDir, key);
      setSortKey(next.sortKey);
      setSortDir(next.sortDir);
    },
    [sortDir, sortKey]
  );

  return { sortedRates, sortKey, sortDir, toggleSort };
}
