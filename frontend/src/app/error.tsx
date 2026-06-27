/** Route-level error boundary for uncaught render errors. */

"use client";

import { ErrorBanner } from "@/components/ErrorBanner";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main style={{ maxWidth: 1200, margin: "2rem auto", padding: "0 1rem" }}>
      <ErrorBanner message={error.message || "Something went wrong loading the dashboard."} onRetry={reset} />
    </main>
  );
}
