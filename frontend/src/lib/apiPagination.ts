/** Pagination helpers for history and ingested API clients. */

/** Normalize DRF absolute next URLs to paths the Next.js proxy can re-fetch. */
export function resolveNextPagePath(next: string, apiUrl: string): string {
  if (!next.startsWith("http")) {
    return next;
  }
  const { pathname, search } = new URL(next);
  if (apiUrl.startsWith("http")) {
    return next;
  }
  const apiPrefix = apiUrl.startsWith("/") ? apiUrl : `/${apiUrl}`;
  if (pathname.startsWith(apiPrefix)) {
    return `${pathname.slice(apiPrefix.length)}${search}`;
  }
  return `${pathname}${search}`;
}

export interface PaginatedPage<T> {
  results: T[];
  next: string | null;
}

/** Walk ?next= links until the API returns a null next page. */
export async function fetchAllPages<T>(
  firstPath: string,
  fetchPage: (path: string) => Promise<PaginatedPage<T>>,
  apiUrl: string,
): Promise<T[]> {
  const results: T[] = [];
  let path: string | null = firstPath;

  while (path !== null) {
    const currentPath: string = path;
    const page = await fetchPage(currentPath);
    results.push(...page.results);
    path = page.next ? resolveNextPagePath(page.next, apiUrl) : null;
  }

  return results;
}
