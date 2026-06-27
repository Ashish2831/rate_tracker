/** Inline empty state for tables and charts. */

import type { ReactNode } from "react";

import styles from "./EmptyState.module.css";

interface Props {
  title: string;
  description: ReactNode;
  icon?: "table" | "chart";
}

function EmptyIcon({ type }: { type: "table" | "chart" }) {
  if (type === "chart") {
    return (
      <svg width="40" height="40" viewBox="0 0 40 40" fill="none" aria-hidden="true">
        <rect x="4" y="28" width="6" height="8" rx="1.5" fill="#cbd5e1" />
        <rect x="14" y="20" width="6" height="16" rx="1.5" fill="#94a3b8" />
        <rect x="24" y="12" width="6" height="24" rx="1.5" fill="#64748b" />
        <path d="M7 26 L17 18 L27 10" stroke="#14b8a6" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" strokeDasharray="4 3" />
      </svg>
    );
  }
  return (
    <svg width="40" height="40" viewBox="0 0 40 40" fill="none" aria-hidden="true">
      <rect x="6" y="8" width="28" height="24" rx="4" stroke="#cbd5e1" strokeWidth="2" />
      <path d="M6 16 H34" stroke="#cbd5e1" strokeWidth="2" />
      <rect x="10" y="21" width="10" height="2" rx="1" fill="#94a3b8" />
      <rect x="10" y="26" width="16" height="2" rx="1" fill="#cbd5e1" />
    </svg>
  );
}

export function EmptyState({ title, description, icon = "table" }: Props) {
  return (
    <div className={styles.container}>
      <div className={styles.iconWrap}>
        <EmptyIcon type={icon} />
      </div>
      <p className={styles.title}>{title}</p>
      <p className={styles.description}>{description}</p>
    </div>
  );
}
