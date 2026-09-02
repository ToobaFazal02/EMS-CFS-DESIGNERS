import csv
import io
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, Response, StreamingResponse
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.orm import selectinload

from app.auth import ALGORITHM, get_current_user, is_manager, require_manager
from app.config import get_settings
from app.db import SessionLocal, get_db
from app.live import live_hub
from app.models import (
    ActivityBucket,
    AuditLog,
    Device,
    Employee,
    Invoice,
    Punch,
    PunchType,
    Project,
    Role,
    Screenshot,
    WindowSample,
    WorkState,
)
from app.schemas import (
    DashFinance,
    DashHourDay,
    DashLateInvoice,
    DashPipeline,
    DashRosterRow,
    DashboardOut,
    DaySessionOut,
    DaySummaryOut,
    LiveEmployeeOut,
    PunchOut,
)
from app.services.duration import hours_to_hm
from app.services.excel_report import build_attendance_xlsx, build_monthly_xlsx
from app.services.hours import (
    activity_fallback_hours,
    clock_for_day,
    compute_sessions,
    day_bounds_utc,
    first_work_at,
    last_work_at,
    merge_punch_lists,
    work_bounds_by_pkt_day,
)
from app.services.payments import delayed_days
from app.services.pdf_report import build_daily_pdf, build_monthly_pdf
from app.services.timeutil import format_pk_time, monday_of, now_pk, to_pk, today_pk
from app.services.validation import parse_day_or_400, reject_future_day, reject_future_month

router = APIRouter(prefix="/api/v1", tags=["manager"])
settings = get_settings()


def _assert_self_or_manager(user: Employee, employee_id: str) -> None:
    if not is_manager(user) and user.id != employee_id:
        raise HTTPException(status_code=403, detail="You can only view your own attendance")


def _present_days(sessions: list[dict]) -> int:
    days: set = set()
    for s in sessions:
        for d in s.get("pkt_days") or []:
            days.add(d)
        if not s.get("pkt_days") and s.get("sign_in") and float(s.get("net_hours") or 0) > 0:
            local = to_pk(s["sign_in"])
            if local:
                days.add(local.date())
    return len(days)


async def _punches_spanning(
    db: AsyncSession,
    employee_id: str,
    start: datetime,
    end: datetime,
) -> list[Punch]:
    """Day/month punches plus Sign In from an open session that started before `start`.

    Without this, overnight work shows clicks on the PDF but Start/End/Sessions stay empty.
    """
    day_punches = list(
        (
            await db.execute(
                select(Punch).where(
                    Punch.employee_id == employee_id,
                    Punch.server_at >= start,
                    Punch.server_at < end,
                )
            )
        )
        .scalars()
        .all()
    )
    last_before = (
        await db.execute(
            select(Punch)
            .where(Punch.employee_id == employee_id, Punch.server_at < start)
            .order_by(Punch.server_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    prior: list[Punch] = []
    if last_before and last_before.type != PunchType.sign_out and last_before.session_id:
        prior = list(
            (
                await db.execute(
                    select(Punch).where(
                        Punch.employee_id == employee_id,
                        Punch.session_id == last_before.session_id,
                    )
                )
            )
            .scalars()
            .all()
        )
    return merge_punch_lists(prior, day_punches)


async def _sessions_capped(
    db: AsyncSession,
    employee_id: str,
    start: datetime,
    end: datetime,
) -> list[dict]:
    """Sessions with hours stopped at last real activity (not sleep / forgotten Sign Out)."""
    punches = await _punches_spanning(db, employee_id, start, end)
    buckets = list(
        (
            await db.execute(
                select(ActivityBucket).where(
                    ActivityBucket.employee_id == employee_id,
                    ActivityBucket.bucket_start >= start,
                    ActivityBucket.bucket_start < end,
                )
            )
        )
        .scalars()
        .all()
    )
    windows = list(
        (
            await db.execute(
                select(WindowSample).where(
                    WindowSample.employee_id == employee_id,
                    WindowSample.sampled_at >= start,
                    WindowSample.sampled_at < end,
                )
            )
        )
        .scalars()
        .all()
    )
    shots = list(
        (
            await db.execute(
                select(Screenshot).where(
                    Screenshot.employee_id == employee_id,
                    Screenshot.captured_at >= start,
                    Screenshot.captured_at < end,
                )
            )
        )
        .scalars()
        .all()
    )
    work_at = last_work_at(buckets=buckets, windows=windows, screenshots=shots)
    work_by_day = work_bounds_by_pkt_day(buckets=buckets, windows=windows, screenshots=shots)
    return compute_sessions(
        punches,
        now=clock_for_day(end),
        last_activity_at=work_at,
        work_by_day=work_by_day,
    )


_DOW = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


def _stale_offline(status: str, last_seen: datetime | None) -> tuple[str, bool]:
    """90s heartbeat stale rule. Second value: clear last_window."""
    if status == "offline":
        return status, False
    if not last_seen:
        return "offline", True
    if (datetime.utcnow() - last_seen).total_seconds() > 90:
        return "offline", True
    return status, False


async def _live_staff(db: AsyncSession) -> list[LiveEmployeeOut]:
    emps = (await db.execute(select(Employee).where(Employee.active == True))).scalars().all()  # noqa: E712
    out: list[LiveEmployeeOut] = []
    for emp in emps:
        if emp.role != Role.employee:
            continue
        devices = list(
            (
                await db.execute(
                    select(Device)
                    .where(Device.employee_id == emp.id, Device.enrolled_at.is_not(None))
                    .order_by(Device.last_seen_at.desc())
                )
            )
            .scalars()
            .all()
        )
        if not devices:
            devices = list(
                (
                    await db.execute(
                        select(Device).where(Device.employee_id == emp.id).order_by(Device.last_seen_at.desc())
                    )
                )
                .scalars()
                .all()
            )
        d = devices[0] if devices else None
        thumb = None
        status = "offline"
        last_window = ""
        last_seen = None
        clicks = keys = idle = 0
        if d:
            status = d.live_status or "offline"
            last_window = d.last_window or ""
            last_seen = d.last_seen_at
            clicks = d.last_clicks_delta
            keys = d.last_keys_delta
            idle = d.idle_seconds
            if d.last_screenshot_id:
                thumb = f"/api/v1/screenshots/{d.last_screenshot_id}/file"
            status, clear_window = _stale_offline(status, last_seen)
            if clear_window:
                last_window = ""
        out.append(
            LiveEmployeeOut(
                employee_id=emp.id,
                code=emp.code,
                full_name=emp.full_name,
                status=status,
                last_window=last_window,
                last_seen_at=last_seen,
                last_clicks_delta=clicks,
                last_keys_delta=keys,
                idle_seconds=idle,
                last_screenshot_url=thumb,
            )
        )
    return out


def _pkt_days(start: date, count: int) -> list[date]:
    return [start + timedelta(days=i) for i in range(count)]


def _day_net_hours(
    punches: list[Punch],
    buckets: list,
    windows: list,
    shots: list,
    day: date,
) -> float:
    """Same hours engine as attendance CSV, for one PKT calendar day."""
    start, end = day_bounds_utc(datetime(day.year, day.month, day.day))
    day_buckets = [b for b in buckets if b.bucket_start and start <= b.bucket_start < end]
    day_windows = [w for w in windows if w.sampled_at and start <= w.sampled_at < end]
    day_shots = [s for s in shots if s.captured_at and start <= s.captured_at < end]
    in_day = [p for p in punches if start <= p.server_at < end]
    earlier = [p for p in punches if p.server_at < start]
    last_before = max(earlier, key=lambda p: p.server_at) if earlier else None
    prior: list[Punch] = []
    if last_before and last_before.type != PunchType.sign_out and last_before.session_id:
        prior = [p for p in punches if p.session_id == last_before.session_id]
    merged = merge_punch_lists(prior, in_day)
    work_at = last_work_at(buckets=day_buckets, windows=day_windows, screenshots=day_shots)
    work_by_day = work_bounds_by_pkt_day(
        buckets=day_buckets, windows=day_windows, screenshots=day_shots
    )
    sessions = compute_sessions(
        merged,
        now=clock_for_day(end),
        last_activity_at=work_at,
        work_by_day=work_by_day,
    )
    net = sum(float(s["net_hours"] or 0) for s in sessions)
    if not sessions:
        clicks = sum(b.mouse_clicks for b in day_buckets)
        keys = sum(b.key_presses for b in day_buckets)
        idle_sec = sum(b.idle_seconds for b in day_buckets)
        if clicks or keys:
            first = first_work_at(buckets=day_buckets, windows=day_windows, screenshots=day_shots)
            net = activity_fallback_hours(first_at=first, last_at=work_at, idle_seconds=idle_sec)
    return round(float(net or 0), 2)


async def _hours_by_day(
    db: AsyncSession,
    emp_ids: list[str],
    days: list[date],
) -> dict[str, dict[date, float]]:
    if not emp_ids or not days:
        return {eid: {} for eid in emp_ids}
    range_start, _ = day_bounds_utc(datetime(days[0].year, days[0].month, days[0].day))
    _, range_end = day_bounds_utc(datetime(days[-1].year, days[-1].month, days[-1].day))
    out: dict[str, dict[date, float]] = {eid: {d: 0.0 for d in days} for eid in emp_ids}
    for eid in emp_ids:
        punches = await _punches_spanning(db, eid, range_start, range_end)
        buckets = list(
            (
                await db.execute(
                    select(ActivityBucket).where(
                        ActivityBucket.employee_id == eid,
                        ActivityBucket.bucket_start >= range_start,
                        ActivityBucket.bucket_start < range_end,
                    )
                )
            )
            .scalars()
            .all()
        )
        windows = list(
            (
                await db.execute(
                    select(WindowSample).where(
                        WindowSample.employee_id == eid,
                        WindowSample.sampled_at >= range_start,
                        WindowSample.sampled_at < range_end,
                    )
                )
            )
            .scalars()
            .all()
        )
        shots = list(
            (
                await db.execute(
                    select(Screenshot).where(
                        Screenshot.employee_id == eid,
                        Screenshot.captured_at >= range_start,
                        Screenshot.captured_at < range_end,
                    )
                )
            )
            .scalars()
            .all()
        )
        for d in days:
            out[eid][d] = _day_net_hours(punches, buckets, windows, shots, d)
    return out


def _hour_days(days: list[date], totals: dict[date, float]) -> list[DashHourDay]:
    return [
        DashHourDay(date=d.isoformat(), label=_DOW[d.weekday()], hours=round(float(totals.get(d) or 0), 2))
        for d in days
    ]


@router.get("/live", response_model=list[LiveEmployeeOut])
async def live_board(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Employee, Depends(require_manager)],
) -> list[LiveEmployeeOut]:
    return await _live_staff(db)


@router.get("/dashboard", response_model=DashboardOut)
async def dashboard_summary(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Employee, Depends(require_manager)],
) -> DashboardOut:
    live = await _live_staff(db)
    staff_count = len(live)
    live_now = sum(1 for r in live if r.status == "working")
    break_idle = sum(1 for r in live if r.status in ("break", "idle"))
    offline = sum(1 for r in live if r.status == "offline" or not r.status)

    projects = list((await db.execute(select(Project))).scalars().all())
    working_n = sum(1 for p in projects if p.work_state == WorkState.working.value)
    waiting_n = sum(1 for p in projects if p.work_state == WorkState.waiting.value)
    hold_n = sum(1 for p in projects if p.work_state == WorkState.on_hold.value)
    done_n = sum(1 for p in projects if p.work_state == WorkState.done.value)
    pipeline = DashPipeline(
        working=working_n,
        waiting=waiting_n,
        on_hold=hold_n,
        done=done_n,
        total=len(projects),
        open=len(projects) - done_n,
    )

    today = today_pk()
    this_mon = monday_of(today)
    last_mon = this_mon - timedelta(days=7)
    this_days = _pkt_days(this_mon, 7)
    last_days = _pkt_days(last_mon, 7)
    all_days = last_days + this_days
    emp_ids = [r.employee_id for r in live]
    by_emp = await _hours_by_day(db, emp_ids, all_days)

    def team_total(d: date) -> float:
        return round(sum(by_emp.get(eid, {}).get(d, 0.0) for eid in emp_ids), 2)

    this_totals = {d: team_total(d) for d in this_days}
    last_totals = {d: team_total(d) for d in last_days}
    through = today.weekday() + 1
    this_so_far = sum(this_totals[d] for d in this_days[:through])
    last_so_far = sum(last_totals[d] for d in last_days[:through])
    hours_today = {eid: by_emp.get(eid, {}).get(today, 0.0) for eid in emp_ids}

    roster = [
        DashRosterRow(
            employee_id=r.employee_id,
            code=r.code,
            full_name=r.full_name,
            status=r.status,
            last_window=r.last_window or "",
            hours_today=round(float(hours_today.get(r.employee_id) or 0), 2),
        )
        for r in live
    ]

    finance: DashFinance | None = None
    if user.role == Role.admin:
        invs = list(
            (await db.execute(select(Invoice).options(selectinload(Invoice.client)))).scalars().all()
        )
        ym = f"{today.year:04d}-{today.month:02d}"
        unpaid_n = 0
        unpaid_by: dict[str, float] = defaultdict(float)
        paid_by: dict[str, float] = defaultdict(float)
        late: list[DashLateInvoice] = []
        for inv in invs:
            amt = float(inv.amount or 0)
            cur = (inv.currency or "USD").upper() or "USD"
            if (inv.status or "") == "paid":
                local = to_pk(inv.invoice_date) if inv.invoice_date else None
                if local and f"{local.year:04d}-{local.month:02d}" == ym:
                    paid_by[cur] += amt
            else:
                unpaid_n += 1
                unpaid_by[cur] += amt
                delay = delayed_days(inv, today=today)
                if delay > 0:
                    late.append(
                        DashLateInvoice(
                            id=inv.id,
                            client_name=(inv.client.name if inv.client else "") or "—",
                            number=inv.number or "",
                            amount=amt,
                            currency=cur,
                            delayed_days=delay,
                        )
                    )
        late.sort(key=lambda x: x.delayed_days, reverse=True)
        currency = "USD"
        if unpaid_by:
            currency = max(unpaid_by, key=lambda c: unpaid_by[c])
        elif paid_by:
            currency = max(paid_by, key=lambda c: paid_by[c])
        finance = DashFinance(
            unpaid_count=unpaid_n,
            unpaid_amount=round(float(unpaid_by.get(currency) or 0), 2),
            paid_month_amount=round(float(paid_by.get(currency) or 0), 2),
            currency=currency,
            late=late[:40],
        )

    generated = now_pk().strftime("%H:%M")
    spark = [this_totals[d] for d in this_days]
    return DashboardOut(
        generated_at=f"Updated {generated} PKT",
        timezone="Asia/Karachi",
        staff_count=staff_count,
        live_now=live_now,
        break_idle=break_idle,
        offline=offline,
        pipeline=pipeline,
        hours_this_week=_hour_days(this_days, this_totals),
        hours_last_week=_hour_days(last_days, last_totals),
        week_delta_hours=round(this_so_far - last_so_far, 1),
        sparkline=[round(x, 2) for x in spark],
        roster=roster,
        finance=finance,
    )


@router.websocket("/ws/live")
async def ws_live(websocket: WebSocket) -> None:
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4401)
        return
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        if payload.get("typ") != "user":
            await websocket.close(code=4401)
            return
        emp_id = payload.get("sub")
        role = (payload.get("role") or "").lower()
        if role not in ("manager", "admin"):
            await websocket.close(code=4403)
            return
        async with SessionLocal() as db:
            emp = await db.get(Employee, emp_id)
            if not emp or not emp.active:
                await websocket.close(code=4401)
                return
            if emp.role not in (Role.manager, Role.admin):
                await websocket.close(code=4403)
                return
    except JWTError:
        await websocket.close(code=4401)
        return

    await websocket.accept()
    q = live_hub.subscribe()
    try:
        while True:
            event = await q.get()
            await websocket.send_json(event)
    except WebSocketDisconnect:
        pass
    finally:
        live_hub.unsubscribe(q)


@router.get("/employees/{employee_id}/day", response_model=DaySummaryOut)
async def employee_day(
    employee_id: str,
    date: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Employee, Depends(get_current_user)],
) -> DaySummaryOut:
    _assert_self_or_manager(user, employee_id)
    try:
        day = datetime.strptime(date, "%Y-%m-%d")
    except ValueError as e:
        raise HTTPException(status_code=400, detail="date must be YYYY-MM-DD") from e
    reject_future_day(day.date())
    start, end = day_bounds_utc(day)
    punches = await _punches_spanning(db, employee_id, start, end)
    buckets = (
        await db.execute(
            select(ActivityBucket).where(
                ActivityBucket.employee_id == employee_id,
                ActivityBucket.bucket_start >= start,
                ActivityBucket.bucket_start < end,
            )
        )
    ).scalars().all()
    windows = (
        await db.execute(
            select(WindowSample).where(
                WindowSample.employee_id == employee_id,
                WindowSample.sampled_at >= start,
                WindowSample.sampled_at < end,
            )
        )
    ).scalars().all()
    shots = (
        await db.execute(
            select(Screenshot).where(
                Screenshot.employee_id == employee_id,
                Screenshot.captured_at >= start,
                Screenshot.captured_at < end,
            )
        )
    ).scalars().all()
    work_at = last_work_at(buckets=list(buckets), windows=list(windows), screenshots=list(shots))
    work_by_day = work_bounds_by_pkt_day(
        buckets=list(buckets), windows=list(windows), screenshots=list(shots)
    )
    sessions = compute_sessions(
        list(punches),
        now=clock_for_day(end),
        last_activity_at=work_at,
        work_by_day=work_by_day,
    )
    clicks = sum(b.mouse_clicks for b in buckets)
    keys = sum(b.key_presses for b in buckets)
    idle_sec = sum(b.idle_seconds for b in buckets)
    net = sum(s["net_hours"] for s in sessions)
    brk = sum(s["break_minutes"] for s in sessions) / 60.0
    if not sessions and (clicks or keys):
        first = first_work_at(buckets=list(buckets), windows=list(windows), screenshots=list(shots))
        net = activity_fallback_hours(first_at=first, last_at=work_at, idle_seconds=idle_sec)
    return DaySummaryOut(
        employee_id=employee_id,
        date=date,
        sessions=[
            DaySessionOut(
                **{
                    k: v
                    for k, v in s.items()
                    if k in ("session_id", "sign_in", "sign_out", "break_minutes", "net_hours", "status")
                }
            )
            for s in sessions
        ],
        net_hours=round(net, 2),
        break_hours=round(brk, 2),
        total_clicks=clicks,
        total_keys=keys,
        idle_minutes=round(idle_sec / 60.0, 1),
        punches=[
            PunchOut(
                id=p.id,
                type=p.type,
                server_at=p.server_at,
                session_id=p.session_id,
                employee_id=p.employee_id,
            )
            for p in punches
            if start <= p.server_at < end
        ],
    )


@router.get("/employees/{employee_id}/screenshots")
async def list_screenshots(
    employee_id: str,
    date: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Employee, Depends(get_current_user)],
) -> list[dict]:
    _assert_self_or_manager(user, employee_id)
    try:
        day = datetime.strptime(date, "%Y-%m-%d")
    except ValueError as e:
        raise HTTPException(status_code=400, detail="date must be YYYY-MM-DD") from e
    reject_future_day(day.date())
    start, end = day_bounds_utc(day)
    shots = (
        await db.execute(
            select(Screenshot)
            .where(
                Screenshot.employee_id == employee_id,
                Screenshot.captured_at >= start,
                Screenshot.captured_at < end,
            )
            .order_by(Screenshot.captured_at)
        )
    ).scalars().all()
    return [
        {
            "id": s.id,
            "captured_at": (
                s.captured_at.isoformat() + "Z"
                if s.captured_at and getattr(s.captured_at, "tzinfo", None) is None
                else (s.captured_at.isoformat() if s.captured_at else None)
            ),
            "url": f"/api/v1/screenshots/{s.id}/file",
            "bytes": s.bytes,
        }
        for s in shots
    ]


@router.get("/screenshots/{screenshot_id}/file")
async def get_screenshot_file(
    screenshot_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Employee, Depends(get_current_user)],
    audit: bool = False,
) -> FileResponse:
    """Live thumbs omit audit=1 (poll every 5s). Day lightbox passes audit=1 once."""
    shot = await db.get(Screenshot, screenshot_id)
    if not shot:
        raise HTTPException(status_code=404, detail="Not found")
    _assert_self_or_manager(user, shot.employee_id)
    root = settings.data_path.resolve()
    path = (root / shot.path).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise HTTPException(status_code=404, detail="File missing")
    if audit and is_manager(user):
        db.add(
            AuditLog(
                actor_id=user.id,
                action="screenshot_view",
                entity="screenshot",
                payload_json=f'{{"screenshot_id":"{screenshot_id}","employee_id":"{shot.employee_id}"}}',
            )
        )
        await db.commit()
    return FileResponse(path, media_type=shot.content_type)


@router.get("/employees/{employee_id}/day.pdf")
async def daily_pdf(
    employee_id: str,
    date: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Employee, Depends(get_current_user)],
    inline: bool = False,
) -> FileResponse:
    _assert_self_or_manager(user, employee_id)
    emp = await db.get(Employee, employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    d = parse_day_or_400(date)
    reject_future_day(d)
    day = datetime(d.year, d.month, d.day)
    start, end = day_bounds_utc(day)
    punches = await _punches_spanning(db, employee_id, start, end)
    buckets = list(
        (
            await db.execute(
                select(ActivityBucket).where(
                    ActivityBucket.employee_id == employee_id,
                    ActivityBucket.bucket_start >= start,
                    ActivityBucket.bucket_start < end,
                )
            )
        ).scalars().all()
    )
    windows = list(
        (
            await db.execute(
                select(WindowSample).where(
                    WindowSample.employee_id == employee_id,
                    WindowSample.sampled_at >= start,
                    WindowSample.sampled_at < end,
                )
            )
        ).scalars().all()
    )
    shots = list(
        (
            await db.execute(
                select(Screenshot).where(
                    Screenshot.employee_id == employee_id,
                    Screenshot.captured_at >= start,
                    Screenshot.captured_at < end,
                )
            )
        ).scalars().all()
    )
    work_at = last_work_at(buckets=buckets, windows=windows, screenshots=shots)
    first_at = first_work_at(buckets=buckets, windows=windows, screenshots=shots)
    work_by_day = work_bounds_by_pkt_day(buckets=buckets, windows=windows, screenshots=shots)
    sessions = compute_sessions(
        punches,
        now=clock_for_day(end),
        last_activity_at=work_at,
        work_by_day=work_by_day,
    )
    title_counts: dict[str, int] = defaultdict(int)
    click_log: list[tuple[str, str, int]] = []
    for w in windows:
        clicks_n = int(w.clicks or 0)
        title_counts[w.title] += clicks_n
        local = to_pk(w.sampled_at) or w.sampled_at
        minute = local.strftime("%Y-%m-%d %H:%M")
        click_log.append((minute, w.title or "", clicks_n))
    click_log.sort(key=lambda x: x[0])
    top = sorted(title_counts.items(), key=lambda x: x[1], reverse=True)
    net = sum(s["net_hours"] for s in sessions)
    brk = sum(s["break_minutes"] for s in sessions) / 60.0
    idle_min = sum(b.idle_seconds for b in buckets) / 60.0
    # Activity without Sign In (agent desync) — still show honest Start/End/Hours
    overview_note = None
    if not sessions and (sum(b.mouse_clicks for b in buckets) or sum(b.key_presses for b in buckets)):
        net = activity_fallback_hours(
            first_at=first_at,
            last_at=work_at,
            idle_seconds=sum(b.idle_seconds for b in buckets),
        )
        overview_note = "No Sign In recorded — hours estimated from activity"
    series_map: dict[str, float] = defaultdict(float)
    for b in buckets:
        local = to_pk(b.bucket_start) or b.bucket_start
        label = local.strftime("%H:%M")
        series_map[label] += float(b.mouse_clicks)
    activity_series = sorted(series_map.items(), key=lambda x: x[0])
    out_path = settings.data_path / "reports" / f"{emp.code}_{date}.pdf"
    build_daily_pdf(
        out_path,
        emp.full_name,
        emp.code,
        date,
        sessions,
        sum(b.mouse_clicks for b in buckets),
        sum(b.key_presses for b in buckets),
        idle_min,
        net,
        brk,
        top,
        activity_series,
        click_log,
        overtime_hours_per_day=float(settings.overtime_hours_per_day),
        first_activity_at=first_at,
        last_activity_at=work_at,
        overview_note=overview_note,
    )
    disposition = "inline" if inline else "attachment"
    # Staff may view only — never force a download attachment
    if user.role == Role.employee:
        disposition = "inline"
    return FileResponse(
        out_path,
        media_type="application/pdf",
        filename=f"daily_{date}.pdf",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "Pragma": "no-cache",
            "Content-Disposition": f'{disposition}; filename="daily_{date}.pdf"',
        },
    )


@router.get("/reports/attendance.csv")
async def attendance_csv(
    date: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Employee, Depends(require_manager)],
) -> StreamingResponse:
    d = parse_day_or_400(date)
    reject_future_day(d)
    day = datetime(d.year, d.month, d.day)
    start, end = day_bounds_utc(day)
    emps = list(
        (await db.execute(select(Employee).where(Employee.role == Role.employee, Employee.active == True))).scalars().all()  # noqa: E712
    )
    # Text date (not Excel date serial) so Excel shows "22 Aug 2026" not ########
    date_label = day.strftime("%d %b %Y")
    buf = io.StringIO()
    buf.write("\ufeff")
    writer = csv.writer(buf)
    writer.writerow(
        ["Code", "Employee", "Date", "Sessions", "Net Work", "Break Time", "First Sign In", "Last Sign Out"]
    )
    for emp in emps:
        sessions = await _sessions_capped(db, emp.id, start, end)
        net = sum(s["net_hours"] for s in sessions)
        brk = sum(s["break_minutes"] for s in sessions) / 60.0
        first_in = format_pk_time(sessions[0]["sign_in"]) if sessions and sessions[0]["sign_in"] else ""
        last_out = ""
        for s in sessions:
            if s["sign_out"]:
                last_out = format_pk_time(s["sign_out"])
        writer.writerow(
            [
                emp.code,
                emp.full_name,
                f"'{date_label}",
                len(sessions),
                hours_to_hm(net),
                hours_to_hm(brk),
                first_in or "—",
                last_out or "—",
            ]
        )
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="attendance_{date}.csv"',
            "Cache-Control": "no-store",
        },
    )


@router.get("/reports/attendance.xlsx")
async def attendance_xlsx(
    date: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Employee, Depends(require_manager)],
) -> Response:
    d = parse_day_or_400(date)
    reject_future_day(d)
    day = datetime(d.year, d.month, d.day)
    start, end = day_bounds_utc(day)
    emps = list(
        (await db.execute(select(Employee).where(Employee.role == Role.employee, Employee.active == True))).scalars().all()  # noqa: E712
    )
    rows = []
    for emp in emps:
        sessions = await _sessions_capped(db, emp.id, start, end)
        net = sum(s["net_hours"] for s in sessions)
        brk = sum(s["break_minutes"] for s in sessions) / 60.0
        first_in = format_pk_time(sessions[0]["sign_in"]) if sessions and sessions[0]["sign_in"] else ""
        last_out = ""
        for s in sessions:
            if s["sign_out"]:
                last_out = format_pk_time(s["sign_out"])
        rows.append(
            {
                "code": emp.code,
                "name": emp.full_name,
                "sessions": len(sessions),
                "net_hours": net,
                "break_hours": brk,
                "sign_in": first_in,
                "sign_out": last_out,
            }
        )
    data = build_attendance_xlsx(rows, day.date())
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="EMS_Attendance_{date}.xlsx"',
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "Pragma": "no-cache",
        },
    )


@router.get("/reports/monthly.csv")
async def monthly_csv(
    year: int,
    month: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Employee, Depends(require_manager)],
) -> StreamingResponse:
    reject_future_month(year, month)
    start, _ = day_bounds_utc(datetime(year, month, 1))
    if month == 12:
        end, _ = day_bounds_utc(datetime(year + 1, 1, 1))
    else:
        end, _ = day_bounds_utc(datetime(year, month + 1, 1))
    emps = list(
        (await db.execute(select(Employee).where(Employee.role == Role.employee, Employee.active == True))).scalars().all()  # noqa: E712
    )
    buf = io.StringIO()
    buf.write("\ufeff")
    writer = csv.writer(buf)
    writer.writerow(
        ["Code", "Employee", "Year", "Month", "Days Present", "Net Work", "Break Time", "Avg / Present Day"]
    )
    month_name = datetime(year, month, 1).strftime("%b")
    for emp in emps:
        sessions = await _sessions_capped(db, emp.id, start, end)
        days = _present_days(sessions)
        net = sum(s["net_hours"] for s in sessions)
        brk = sum(s["break_minutes"] for s in sessions) / 60.0
        avg = (net / days) if days else 0.0
        writer.writerow(
            [
                emp.code,
                emp.full_name,
                year,
                month_name,
                days,
                hours_to_hm(net),
                hours_to_hm(brk),
                hours_to_hm(avg),
            ]
        )
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="monthly_{year}_{month:02d}.csv"',
            "Cache-Control": "no-store",
        },
    )


@router.get("/reports/monthly.xlsx")
async def monthly_xlsx(
    year: int,
    month: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Employee, Depends(require_manager)],
) -> Response:
    reject_future_month(year, month)
    start, _ = day_bounds_utc(datetime(year, month, 1))
    if month == 12:
        end, _ = day_bounds_utc(datetime(year + 1, 1, 1))
    else:
        end, _ = day_bounds_utc(datetime(year, month + 1, 1))
    emps = list(
        (await db.execute(select(Employee).where(Employee.role == Role.employee, Employee.active == True))).scalars().all()  # noqa: E712
    )
    rows = []
    for emp in emps:
        sessions = await _sessions_capped(db, emp.id, start, end)
        days = _present_days(sessions)
        net = sum(s["net_hours"] for s in sessions)
        brk = sum(s["break_minutes"] for s in sessions) / 60.0
        rows.append(
            {
                "code": emp.code,
                "name": emp.full_name,
                "days": days,
                "net_hours": net,
                "break_hours": brk,
            }
        )
    data = build_monthly_xlsx(rows, year, month)
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="EMS_Monthly_{year}_{month:02d}.xlsx"',
            "Cache-Control": "no-store, no-cache, must-revalidate",
        },
    )


@router.get("/reports/monthly.pdf")
async def monthly_pdf(
    year: int,
    month: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Employee, Depends(require_manager)],
    inline: bool = False,
) -> FileResponse:
    reject_future_month(year, month)
    start, _ = day_bounds_utc(datetime(year, month, 1))
    if month == 12:
        end, _ = day_bounds_utc(datetime(year + 1, 1, 1))
    else:
        end, _ = day_bounds_utc(datetime(year, month + 1, 1))
    emps = list(
        (await db.execute(select(Employee).where(Employee.role == Role.employee, Employee.active == True))).scalars().all()  # noqa: E712
    )
    rows = []
    for emp in emps:
        sessions = await _sessions_capped(db, emp.id, start, end)
        days = _present_days(sessions)
        net = sum(s["net_hours"] for s in sessions)
        brk = sum(s["break_minutes"] for s in sessions) / 60.0
        rows.append(
            {
                "code": emp.code,
                "name": emp.full_name,
                "days": days,
                "net_hours": net,
                "break_hours": brk,
            }
        )
    out_path = settings.data_path / "reports" / f"monthly_{year}_{month:02d}.pdf"
    build_monthly_pdf(
        out_path,
        year,
        month,
        rows,
        overtime_hours_per_day=float(settings.overtime_hours_per_day),
    )
    disposition = "inline" if inline else "attachment"
    return FileResponse(
        out_path,
        media_type="application/pdf",
        filename=f"monthly_{year}_{month:02d}.pdf",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "Content-Disposition": f'{disposition}; filename="monthly_{year}_{month:02d}.pdf"',
        },
    )
