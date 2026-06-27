/** Human-readable labels for snake_case rate_type slugs. */

const ACRONYMS = new Set(["apr", "apy", "cd", "ira"]);

export function formatRateType(slug: string): string {
  return slug
    .split("_")
    .map((word) => {
      const lower = word.toLowerCase();
      if (ACRONYMS.has(lower)) return lower.toUpperCase();
      if (/^\d/.test(word)) return word;
      return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
    })
    .join(" ");
}

export function formatRateValue(value: number | null): string {
  if (value === null) return "—";
  return `${Number(value).toFixed(2)}%`;
}
