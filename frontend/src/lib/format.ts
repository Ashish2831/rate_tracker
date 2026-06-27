/** Human-readable labels for snake_case rate_type slugs. */

export function formatRateType(slug: string): string {
  return slug.replace(/_/g, " ");
}
