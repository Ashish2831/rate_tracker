/** Dashboard tab definitions — shared by tab bar and panel headers. */

export type DashboardTab = "dashboard" | "latest-by-provider" | "history" | "ingested";

export interface DashboardTabConfig {
  id: DashboardTab;
  label: string;
  title: string;
  description: string;
}

export const DASHBOARD_TABS: DashboardTabConfig[] = [
  {
    id: "dashboard",
    label: "Dashboard",
    title: "Dashboard Overview",
    description: "Latest rate per provider — summary cards with best rate and product count",
  },
  {
    id: "latest-by-provider",
    label: "Latest Rate By Provider",
    title: "Latest Rate By Provider",
    description: "Full comparison table of latest rates grouped by provider and product type",
  },
  {
    id: "history",
    label: "30-Day History",
    title: "30-Day Rate History",
    description: "Rate change over the last 30 days for a selected provider and type",
  },
  {
    id: "ingested",
    label: "Ingested (24h)",
    title: "Ingested in Last 24 Hours",
    description: "Records ingested in the 24-hour window ending at the latest ingestion batch",
  },
];

export function getDashboardTab(id: DashboardTab): DashboardTabConfig {
  const tab = DASHBOARD_TABS.find((entry) => entry.id === id);
  if (!tab) {
    throw new Error(`Unknown dashboard tab: ${id}`);
  }
  return tab;
}
