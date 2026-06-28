/** Dashboard filter types — searchable combobox and toolbar props. */

/** Single selectable value in a searchable filter dropdown. */
export interface FilterOption {
  /** API filter value (provider name or rate_type slug). */
  value: string;
  /** Human-readable label shown in the input and list. */
  label: string;
}

export interface SearchableFilterProps {
  label: string;
  /** Placeholder and label for the empty / “all” option. */
  allLabel: string;
  options: FilterOption[];
  /** Current filter value; empty string means no filter applied. */
  value: string;
  onChange: (value: string) => void;
}

export interface FilterToolbarProps {
  /** Distinct providers from GET /api/rates/filters. */
  providers: string[];
  /** Distinct rate types from GET /api/rates/filters. */
  rateTypes: string[];
  providerFilter: string;
  typeFilter: string;
  onProviderChange: (value: string) => void;
  onTypeChange: (value: string) => void;
}
