"""Hours: punches + proof-of-work. Sleep / forgotten Sign Out must not inflate totals."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

from app.models import Punch, PunchType
from app.services.timeutil import PK, to_pk


def first_work_at(
    *,
    buckets: list | None = None,
    windows: list | None = None,
    screenshots: list | None = None,
) -> datetime | None:
    """Earliest proof of work in the given samples."""
    earliest: datetime | None = None
    for b in buckets or []:
        if (b.mouse_clicks or b.key_presses) and b.bucket_start:
            if earliest is None or b.bucket_start < earliest:
                earliest = b.bucket_start
    for w in windows or []:
        if w.sampled_at and (w.clicks or 0) > 0:
            if earliest is None or w.sampled_at < earliest:
                earliest = w.sampled_at
    for s in screenshots or []:
        if s.captured_at:
            if earliest is None or s.captured_at < earliest:
                earliest = s.captured_at
    return earliest


def last_work_at(
    *,
    buckets: list | None = None,
    windows: list | None = None,
    screenshots: list | None = None,
) -> datetime | None:
    """Last time we have proof of work — not idle heartbeats after wake."""
    latest: datetime | None = None
    has_fine = any((w.sampled_at and (w.clicks or 0) > 0) for w in (windows or []))
    for b in buckets or []:
        if (b.mouse_clicks or b.key_presses) and b.bucket_start:
            # Prefer window samples when present; otherwise bucket end is floor+30m.
            end = b.bucket_start if has_fine else (b.bucket_start + timedelta(minutes=30))
            if latest is None or end > latest:
                latest = end
    for w in windows or []:
        if w.sampled_at and (w.clicks or 0) > 0:
            if latest is None or w.sampled_at > latest:
                latest = w.sampled_at
    for s in screenshots or []:
        if s.captured_at:
            if latest is None or s.captured_at > latest:
                latest = s.captured_at
    return latest


def work_bounds_by_pkt_day(
    *,
    buckets: list | None = None,
    windows: list | None = None,
    screenshots: list | None = None,
) -> dict[date, tuple[datetime, datetime]]:
    """PKT calendar day → (first_work_utc, last_work_utc)."""
    firsts: dict[date, datetime] = {}
    lasts: dict[date, datetime] = {}

    def _touch(ts: datetime, end: datetime | None = None) -> None:
        local = to_pk(ts)
        if not local:
            return
        d = local.date()
        if d not in firsts or ts < firsts[d]:
            firsts[d] = ts
        stop = end or ts
        if d not in lasts or stop > lasts[d]:
            lasts[d] = stop

    has_fine = any((w.sampled_at and (w.clicks or 0) > 0) for w in (windows or []))
    for b in buckets or []:
        if (b.mouse_clicks or b.key_presses) and b.bucket_start:
            _touch(
                b.bucket_start,
                b.bucket_start if has_fine else (b.bucket_start + timedelta(minutes=30)),
            )
    for w in windows or []:
        if w.sampled_at and (w.clicks or 0) > 0:
            _touch(w.sampled_at)
    for s in screenshots or []:
        if s.captured_at:
            _touch(s.captured_at)
    return {d: (firsts[d], lasts[d]) for d in firsts}


def _break_seconds_in_window(
    items: list[Punch],
    win_start: datetime,
    win_end: datetime,
) -> float:
    total = 0.0
    open_break: datetime | None = None
    for p in items:
        if p.type == PunchType.break_in:
            open_break = p.server_at
        elif p.type == PunchType.break_out and open_break is not None:
            b0 = max(open_break, win_start)
            b1 = min(p.server_at, win_end)
            if b1 > b0:
                total += (b1 - b0).total_seconds()
            open_break = None
    if open_break is not None:
        b0 = max(open_break, win_start)
        b1 = win_end
        if b1 > b0:
            total += min((b1 - b0).total_seconds(), 90 * 60)
    return total


def compute_sessions(
    punches: list[Punch],
    now: datetime | None = None,
    *,
    last_activity_at: datetime | None = None,
    stale_after_seconds: int = 10 * 60,
    work_by_day: dict[date, tuple[datetime, datetime]] | None = None,
) -> list[dict]:
    """Group punches into sessions; net hours + completed breaks only.

    When `work_by_day` is provided (recommended for reports), open / multi-day
    sessions are split by PKT calendar day and only count hours between that
    day's first and last **proof of work**. Sleep nights with no clicks do not
    accrue. Without `work_by_day`, falls back to single-span accrual capped at
    `last_activity_at` (legacy day view).
    """
    now = now or datetime.utcnow()

    by_session: dict[str, list[Punch]] = defaultdict(list)
    for p in sorted(punches, key=lambda x: x.server_at):
        by_session[p.session_id].append(p)

    sessions: list[dict] = []

    if work_by_day is not None:
        for sid, items in by_session.items():
            sign_in = next((p.server_at for p in items if p.type == PunchType.sign_in), None)
            sign_out = next((p.server_at for p in reversed(items) if p.type == PunchType.sign_out), None)
            if not sign_in:
                continue

            local_in = to_pk(sign_in)
            if not local_in:
                continue
            end_anchor = sign_out or now
            local_end = to_pk(end_anchor)
            if not local_end:
                continue

            day = local_in.date()
            last_day = local_end.date()
            total_net = 0.0
            total_break_min = 0.0
            day_parts = 0
            pkt_days: list = []
            on_break = False
            open_break: datetime | None = None
            for p in items:
                if p.type == PunchType.break_in:
                    open_break = p.server_at
                    on_break = True
                elif p.type == PunchType.break_out:
                    open_break = None
                    on_break = False
            if sign_out:
                on_break = False

            while day <= last_day:
                day_start_pk = datetime(day.year, day.month, day.day, 0, 0, 0, tzinfo=PK)
                day_end_pk = day_start_pk + timedelta(days=1)
                day_start = day_start_pk.astimezone(timezone.utc).replace(tzinfo=None)
                day_end = day_end_pk.astimezone(timezone.utc).replace(tzinfo=None)

                fw_lw = work_by_day.get(day)
                in_day = to_pk(sign_in) is not None and to_pk(sign_in).date() == day
                if in_day:
                    start = max(sign_in, day_start)
                    # Morning idle before first click does not count
                    if fw_lw:
                        start = max(start, fw_lw[0])
                else:
                    # Continuing session — only count if there is work evidence this day
                    if not fw_lw:
                        day += timedelta(days=1)
                        continue
                    start = max(fw_lw[0], day_start)

                out_day = sign_out and to_pk(sign_out) is not None and to_pk(sign_out).date() == day
                if out_day:
                    end = sign_out
                    # Forgotten late Sign Out must not inflate past last proof of work
                    if fw_lw:
                        end = min(end, fw_lw[1])
                elif fw_lw:
                    end = min(fw_lw[1], day_end, now)
                else:
                    day += timedelta(days=1)
                    continue

                start = max(start, day_start)
                end = min(end, day_end, now)
                if end <= start:
                    day += timedelta(days=1)
                    continue

                brk = _break_seconds_in_window(items, start, end)
                net = max((end - start).total_seconds() - brk, 0.0)
                total_net += net
                total_break_min += brk / 60.0
                day_parts += 1
                pkt_days.append(day)
                day += timedelta(days=1)

            if sign_out:
                status = "closed"
            elif on_break:
                status = "on_break"
            elif day_parts == 0:
                status = "incomplete"
            elif local_end.date() < (to_pk(now) or local_end).date():
                status = "inactive"
            else:
                status = "open"

            sessions.append(
                {
                    "session_id": sid,
                    "sign_in": sign_in,
                    "sign_out": sign_out,
                    "break_minutes": round(total_break_min, 2),
                    "net_hours": round(total_net / 3600.0, 2),
                    "status": status,
                    "accrual_stopped_at": None,
                    "days_counted": day_parts,
                    "pkt_days": pkt_days,
                }
            )
        sessions.sort(key=lambda s: s["sign_in"] or datetime.min)
        return sessions

    # --- Legacy single-span path (day detail when work_by_day not passed) ---
    accrual_now = now
    accrual_capped = False
    if last_activity_at is not None:
        age = (now - last_activity_at).total_seconds()
        if age >= stale_after_seconds and last_activity_at < now:
            accrual_now = last_activity_at
            accrual_capped = True

    for sid, items in by_session.items():
        sign_in = next((p.server_at for p in items if p.type == PunchType.sign_in), None)
        sign_out = next((p.server_at for p in reversed(items) if p.type == PunchType.sign_out), None)
        break_seconds = 0.0
        open_break: datetime | None = None
        on_break = False
        for p in items:
            if p.type == PunchType.break_in:
                open_break = p.server_at
                on_break = True
            elif p.type == PunchType.break_out and open_break:
                break_seconds += (p.server_at - open_break).total_seconds()
                open_break = None
                on_break = False
        if on_break and open_break and not sign_out:
            capped = min((accrual_now - open_break).total_seconds(), 90 * 60)
            break_seconds += max(capped, 0.0)

        if sign_in and sign_out:
            gross = (sign_out - sign_in).total_seconds()
        elif sign_in:
            end = max(accrual_now, sign_in)
            gross = max((end - sign_in).total_seconds(), 0.0)
        else:
            gross = 0.0
        net = max(gross - break_seconds, 0.0)
        sessions.append(
            {
                "session_id": sid,
                "sign_in": sign_in,
                "sign_out": sign_out,
                "break_minutes": round(break_seconds / 60.0, 2),
                "net_hours": round(net / 3600.0, 2),
                "status": (
                    "closed"
                    if sign_out
                    else (
                        "on_break"
                        if on_break
                        else ("inactive" if accrual_capped and sign_in else ("open" if sign_in else "incomplete"))
                    )
                ),
                "accrual_stopped_at": accrual_now if accrual_capped and sign_in and not sign_out else None,
            }
        )
    sessions.sort(key=lambda s: s["sign_in"] or datetime.min)
    return sessions


def clock_for_day(day_end_utc: datetime, now: datetime | None = None) -> datetime:
    """For past calendar days, do not accrue open sessions past midnight."""
    now = now or datetime.utcnow()
    if day_end_utc <= now:
        return day_end_utc - timedelta(seconds=1)
    return now


def day_bounds_utc(day: datetime) -> tuple[datetime, datetime]:
    """Calendar day in Asia/Karachi → UTC naive range for DB queries."""
    start_pk = datetime(day.year, day.month, day.day, 0, 0, 0, tzinfo=PK)
    end_pk = start_pk + timedelta(days=1)
    start = start_pk.astimezone(timezone.utc).replace(tzinfo=None)
    end = end_pk.astimezone(timezone.utc).replace(tzinfo=None)
    return start, end


def merge_punch_lists(*groups: list[Punch]) -> list[Punch]:
    by_id: dict[str, Punch] = {}
    for group in groups:
        for p in group:
            by_id[p.id] = p
    return sorted(by_id.values(), key=lambda p: p.server_at)


def activity_fallback_hours(
    *,
    first_at: datetime | None,
    last_at: datetime | None,
    idle_seconds: float = 0.0,
) -> float:
    """When clicks exist but Sign In was never recorded, estimate net from proof-of-work span."""
    if not first_at or not last_at or last_at <= first_at:
        return 0.0
    gross = (last_at - first_at).total_seconds()
    return round(max(gross - max(idle_seconds, 0.0), 0.0) / 3600.0, 2)
