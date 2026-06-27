/** Accessible tab navigation for the four dashboard views. */

import { DASHBOARD_TABS, DashboardTab } from "@/constants/dashboardTabs";
import styles from "@/app/page.module.css";

interface Props {
  activeTab: DashboardTab;
  onTabChange: (tab: DashboardTab) => void;
}

export function TabBar({ activeTab, onTabChange }: Props) {
  return (
    <div className={styles.tabs} role="tablist" aria-label="Dashboard views">
      {DASHBOARD_TABS.map((tab) => (
        <button
          key={tab.id}
          type="button"
          role="tab"
          id={`tab-${tab.id}`}
          aria-selected={activeTab === tab.id}
          aria-controls={`panel-${tab.id}`}
          className={activeTab === tab.id ? styles.tabActive : styles.tab}
          onClick={() => onTabChange(tab.id)}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
