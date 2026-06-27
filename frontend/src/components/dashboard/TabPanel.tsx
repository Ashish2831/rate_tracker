/** Reusable tab panel shell — title, description, optional count badge, and content. */

import { ReactNode } from "react";

import { DashboardTab } from "@/constants/dashboardTabs";
import styles from "@/app/page.module.css";

interface Props {
  tabId: DashboardTab;
  active: boolean;
  title: string;
  description: string;
  badge?: ReactNode;
  children: ReactNode;
}

export function TabPanel({ tabId, active, title, description, badge, children }: Props) {
  if (!active) {
    return null;
  }

  return (
    <section
      className={styles.card}
      role="tabpanel"
      id={`panel-${tabId}`}
      aria-labelledby={`tab-${tabId}`}
    >
      <div className={styles.cardHeader}>
        <div>
          <h2>{title}</h2>
          <p className={styles.cardDescription}>{description}</p>
        </div>
        {badge}
      </div>
      {children}
    </section>
  );
}
