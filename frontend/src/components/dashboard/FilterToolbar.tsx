/** Shared provider and rate-type filters with search (server-side filtering via API). */

import { useMemo } from "react";

import { SearchableFilter } from "@/components/dashboard/SearchableFilter";
import { FilterToolbarProps } from "@/interfaces/filters";
import { formatRateType } from "@/lib/format";
import styles from "@/app/page.module.css";

export function FilterToolbar({
  providers,
  rateTypes,
  providerFilter,
  typeFilter,
  onProviderChange,
  onTypeChange,
}: FilterToolbarProps) {
  // Map API strings to { value, label } pairs for the combobox.
  const providerOptions = useMemo(
    () => providers.map((provider) => ({ value: provider, label: provider })),
    [providers],
  );
  const rateTypeOptions = useMemo(
    () =>
      rateTypes.map((rateType) => ({
        value: rateType,
        label: formatRateType(rateType),
      })),
    [rateTypes],
  );

  return (
    <section className={styles.toolbar} aria-label="Filters">
      <SearchableFilter
        label="Provider"
        allLabel="All providers"
        options={providerOptions}
        value={providerFilter}
        onChange={onProviderChange}
      />
      <SearchableFilter
        label="Rate type"
        allLabel="All types"
        options={rateTypeOptions}
        value={typeFilter}
        onChange={onTypeChange}
      />
    </section>
  );
}
