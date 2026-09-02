type Props = {
  busy?: boolean;
  onClick: () => void;
  idleLabel?: string;
  busyLabel?: string;
};

export function RefreshButton({ busy = false, onClick, idleLabel = "Refresh", busyLabel = "Refreshing…" }: Props) {
  return (
    <button type="button" className="btn-refresh" onClick={onClick} disabled={busy}>
      <svg className={busy ? "is-spin" : ""} width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden>
        <path
          d="M20 12a8 8 0 10-2.34 5.66M20 12V6m0 6h-6"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      <span>{busy ? busyLabel : idleLabel}</span>
    </button>
  );
}
