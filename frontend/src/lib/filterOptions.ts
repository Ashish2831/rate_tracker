/** Client-side option filtering for searchable dashboard filters. */

import { FilterOption } from "@/interfaces/filters";

/** True when query is empty or matches value/label (case-insensitive substring). */
export function matchesFilterOption(query: string, value: string, label: string): boolean {
  const normalized = query.trim().toLowerCase();
  if (!normalized) return true;
  return value.toLowerCase().includes(normalized) || label.toLowerCase().includes(normalized);
}

/** Subset of options matching the current search query. */
export function filterOptions(query: string, options: FilterOption[]): FilterOption[] {
  return options.filter((option) => matchesFilterOption(query, option.value, option.label));
}

/** Resolve typed text to an option on blur — requires exact value or label match. */
export function resolveFilterOption(
  query: string,
  options: FilterOption[],
): FilterOption | null {
  const normalized = query.trim().toLowerCase();
  if (!normalized) return null;
  return (
    options.find(
      (option) =>
        option.label.toLowerCase() === normalized || option.value.toLowerCase() === normalized,
    ) ?? null
  );
}
