/** Route-level loading UI while the dashboard page bundle loads. */

import { LoadingState } from "@/components/LoadingState";

export default function Loading() {
  return <LoadingState message="Loading dashboard..." />;
}
