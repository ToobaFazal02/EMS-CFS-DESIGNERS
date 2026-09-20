import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  fetchNotificationUnreadCount,
  fetchNotifications,
  markAllNotificationsRead,
  markNotificationsRead,
  type OfficeNotification,
} from "../api";

import { armNotifyAudioUnlock, playNotifyChime, unlockNotifyAudio } from "../notifyAudio";

function relativeTime(iso: string): string {
  try {
    const t = new Date(iso.endsWith("Z") ? iso : `${iso}Z`).getTime();
    const sec = Math.max(0, Math.round((Date.now() - t) / 1000));
    if (sec < 60) return "just now";
    if (sec < 3600) return `${Math.floor(sec / 60)}m ago`;
    if (sec < 86400) return `${Math.floor(sec / 3600)}h ago`;
    return `${Math.floor(sec / 86400)}d ago`;
  } catch {
    return "";
  }
}

/**
 * Office notification center (research-backed inbox pattern):
 * bell + capped unread badge, list, mark-one / mark-all, polling.
 * Admin / Manager / HR / Demo only.
 */
export function NotifyBell() {
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<OfficeNotification[]>([]);
  const [unread, setUnread] = useState(0);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const wrapRef = useRef<HTMLDivElement>(null);
  const primedRef = useRef(false);

  const refresh = useCallback(async () => {
    try {
      const [list, count] = await Promise.all([
        fetchNotifications({ limit: 30 }),
        fetchNotificationUnreadCount(),
      ]);
      setItems(list);
      setUnread((prev) => {
        if (primedRef.current && count > prev && document.visibilityState === "visible") {
          playNotifyChime();
        }
        primedRef.current = true;
        return count;
      });
      setErr("");
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Could not load alerts");
    }
  }, []);

  useEffect(() => armNotifyAudioUnlock(), []);

  useEffect(() => {
    void refresh();
    const t = window.setInterval(() => void refresh(), 45000);
    return () => window.clearInterval(t);
  }, [refresh]);

  useEffect(() => {
    if (!open) return;
    function onDoc(e: MouseEvent) {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) setOpen(false);
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("click", onDoc);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("click", onDoc);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  async function onOpen() {
    unlockNotifyAudio();
    setOpen((v) => !v);
    if (!open) void refresh();
  }

  async function onMarkAll() {
    setBusy(true);
    try {
      await markAllNotificationsRead();
      setItems((prev) => prev.map((n) => ({ ...n, read: true })));
      setUnread(0);
    } finally {
      setBusy(false);
    }
  }

  async function onItemClick(n: OfficeNotification) {
    if (!n.read) {
      setItems((prev) => prev.map((x) => (x.id === n.id ? { ...x, read: true } : x)));
      setUnread((u) => Math.max(0, u - 1));
      void markNotificationsRead([n.id]);
    }
    setOpen(false);
  }

  const badge = unread > 9 ? "9+" : unread > 0 ? String(unread) : "";

  return (
    <div className="notify-wrap" ref={wrapRef}>
      <button
        type="button"
        className="notify-bell"
        aria-label={unread ? `Notifications, ${unread} unread` : "Notifications"}
        aria-expanded={open}
        onClick={(e) => {
          e.stopPropagation();
          void onOpen();
        }}
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden>
          <path
            d="M12 3a5 5 0 00-5 5v2.5c0 .8-.3 1.6-.8 2.2L5 14.5h14l-1.2-1.8c-.5-.6-.8-1.4-.8-2.2V8a5 5 0 00-5-5z"
            stroke="currentColor"
            strokeWidth="1.7"
            strokeLinejoin="round"
          />
          <path d="M9.5 17a2.5 2.5 0 005 0" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
        </svg>
        {badge ? <span className="notify-badge">{badge}</span> : null}
      </button>
      {open ? (
        <div className="notify-panel" role="dialog" aria-label="Office notifications">
          <div className="notify-panel-head">
            <strong>Alerts</strong>
            <button type="button" className="notify-mark-all" disabled={busy || unread === 0} onClick={() => void onMarkAll()}>
              Mark all read
            </button>
          </div>
          {err ? <p className="notify-empty">{err}</p> : null}
          {!err && !items.length ? <p className="notify-empty">No office alerts yet.</p> : null}
          <ul className="notify-list">
            {items.map((n) => {
              const inner = (
                <>
                  <span className={`notify-kind notify-kind-${n.kind || "info"}`}>{n.kind || "info"}</span>
                  <strong className={!n.read ? "is-unread" : undefined}>{n.title}</strong>
                  {n.body ? <span className="notify-body">{n.body}</span> : null}
                  <span className="notify-time">{relativeTime(n.created_at)}</span>
                </>
              );
              return (
                <li key={n.id} className={!n.read ? "is-unread" : undefined}>
                  {n.href ? (
                    <Link to={n.href} onClick={() => void onItemClick(n)}>
                      {inner}
                    </Link>
                  ) : (
                    <button type="button" className="notify-row-btn" onClick={() => void onItemClick(n)}>
                      {inner}
                    </button>
                  )}
                </li>
              );
            })}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
