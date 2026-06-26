import styles from "./LoadingState.module.css";

interface Props {
  message?: string;
}

export function LoadingState({ message = "Loading..." }: Props) {
  return (
    <div className={styles.container} role="status" aria-live="polite">
      <div className={styles.spinner} />
      <p>{message}</p>
    </div>
  );
}
