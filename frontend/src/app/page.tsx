/**
 * Server page shell — streams static HTML, hydrates the interactive dashboard island.
 */

import { DashboardClient } from "@/components/DashboardClient";
import { QueryProvider } from "@/components/QueryProvider";

export default function DashboardPage() {
  return (
    <QueryProvider>
      <DashboardClient />
    </QueryProvider>
  );
}
