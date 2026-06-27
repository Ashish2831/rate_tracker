/** Clickable table header cell with aria-sort and sort direction indicator. */

import { ReactNode } from "react";

import { SortDir, SortKey } from "@/interfaces/rates";
import { SortIndicator } from "@/components/RateTable/SortIndicator";
import { ariaSortValue } from "@/components/RateTable/utils";

interface Props {
  label: ReactNode;
  columnKey: SortKey;
  activeKey: SortKey;
  sortDir: SortDir;
  onSort: (key: SortKey) => void;
}

export function SortableHeader({ label, columnKey, activeKey, sortDir, onSort }: Props) {
  return (
    <th aria-sort={ariaSortValue(columnKey, activeKey, sortDir)}>
      <button type="button" onClick={() => onSort(columnKey)}>
        {label} <SortIndicator active={activeKey === columnKey} dir={sortDir} />
      </button>
    </th>
  );
}
