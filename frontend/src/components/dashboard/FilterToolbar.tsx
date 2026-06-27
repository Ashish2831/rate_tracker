/** Shared provider and rate-type filter dropdowns (server-side filtering via API). */

import { formatRateType } from "@/lib/format";
import styles from "@/app/page.module.css";

interface Props {
  providers: string[];
  rateTypes: string[];
  providerFilter: string;
  typeFilter: string;
  onProviderChange: (value: string) => void;
  onTypeChange: (value: string) => void;
}

export function FilterToolbar({
  providers,
  rateTypes,
  providerFilter,
  typeFilter,
  onProviderChange,
  onTypeChange,
}: Props) {
  return (
    <section className={styles.toolbar} aria-label="Filters">
      <label className={styles.toolbarLabel}>
        Provider
        <select
          className={styles.select}
          value={providerFilter}
          onChange={(e) => onProviderChange(e.target.value)}
        >
          <option value="">All providers</option>
          {providers.map((provider) => (
            <option key={provider} value={provider}>
              {provider}
            </option>
          ))}
        </select>
      </label>
      <label className={styles.toolbarLabel}>
        Rate type
        <select
          className={styles.select}
          value={typeFilter}
          onChange={(e) => onTypeChange(e.target.value)}
        >
          <option value="">All types</option>
          {rateTypes.map((rateType) => (
            <option key={rateType} value={rateType}>
              {formatRateType(rateType)}
            </option>
          ))}
        </select>
      </label>
    </section>
  );
}
