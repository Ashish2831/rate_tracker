/** Shared error message extraction for data-fetching hooks. */

import { ApiError } from "@/lib/api";

export function getErrorMessage(error: unknown, fallback: string): string {
  return error instanceof ApiError ? error.message : fallback;
}
