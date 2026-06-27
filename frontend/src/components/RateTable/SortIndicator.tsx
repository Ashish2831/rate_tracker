/** Visual sort direction indicator for table column headers. */

import { SortDir } from "@/interfaces/rates";
import styles from "./RateTable.module.css";

interface Props {
  active: boolean;
  dir: SortDir;
}

export function SortIndicator({ active, dir }: Props) {
  if (!active) {
    return (
      <span className={styles.sort} aria-hidden="true">
        ↕
      </span>
    );
  }
  return (
    <span className={`${styles.sort} ${styles.sortActive}`} aria-hidden="true">
      {dir === "asc" ? "↑" : "↓"}
    </span>
  );
}
