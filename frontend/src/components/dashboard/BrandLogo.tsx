/** Brand mark shown in the dashboard header. */

import styles from "@/app/page.module.css";

export function BrandLogo() {
  return (
    <div className={styles.logo} aria-hidden="true">
      <svg viewBox="0 0 24 24" fill="none">
        <path
          d="M3 17 L7 12 L10 14.5 L16 7 L21 11"
          stroke="#fff"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <circle cx="21" cy="11" r="1.5" fill="#99f6e4" />
      </svg>
    </div>
  );
}
