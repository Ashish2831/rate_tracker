/** Inline error display with optional retry action. */

import styles from "./ErrorBanner.module.css";

interface Props {
  message: string;
  onRetry?: () => void;
}

export function ErrorBanner({ message, onRetry }: Props) {
  return (
    <div className={styles.banner} role="alert">
      <div>
        <strong>Something went wrong</strong>
        <p>{message}</p>
      </div>
      {onRetry && (
        <button type="button" onClick={onRetry} className={styles.retry}>
          Retry
        </button>
      )}
    </div>
  );
}
