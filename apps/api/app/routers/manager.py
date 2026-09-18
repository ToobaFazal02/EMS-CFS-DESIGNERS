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

from app.auth import ALGORITHM, get_current_user, is_finance, is_manager, is_partner, require_manager, require_office_or_demo
from app.services.data_scope import wants_demo_rows
from app.config import get_settings
from app.db import SessionLocal, get_db
from app.live import live_hub
from app.models import (
    ActivityBucket,
    AuditLog,
    Device,
    Employee,
    Invoice,
    Project,
    ProjectProgress,
    Punch,
    PunchType,
    Role,
    Screenshot,
    WindowSample,
    WorkState,
)
from app.schemas import (
    DashFinance,
    DashHourDay,
    DashLateInvoice,
    DashPartnerShares,
    DashPipeline,
    DashProgressRow,
    DashRosterRow,
    DashboardOut,
    DaySessionOut,
    DaySummaryOut,
    LiveEmployeeOut,
    MeAttendanceDay,
    MeAttendanceOut,
    PunchOut,
)
from app.services.duration import hours_to_hm
from app.services.excel_report import build_attendance_xlsx, build_monthly_xlsx
from app.services.hours import (
    clock_for_day,
    compute_sessions,
    day_bounds_utc,
    first_work_at,
    inferred_work_session,
    last_work_at,
    merge_punch_lists,
    work_bounds_by_pkt_day,
)
from app.services.partner_shares import compute_partner_shares
from app.services.payments import delayed_days
from app.services.pdf_report import build_daily_pdf, build_monthly_pdf, build_personal_monthly_pdf
from app.services.timeutil import format_pk_time, monday_of, now_pk, to_pk, today_pk
from app.services.validation import parse_day_or_400, reject_future_day, reject_future_month

router = APIRouter(prefix="/api/v1", tags=["manager"])
settings = get_settings()


async def _report_staff(db: AsyncSession, user: Employee) -> list[Employee]:
    """Active staff for reports — demo login only sees sample employees."""
    demo = wants_demo_rows(user)
    return list(
        (
            await db.execute(
                select(Employee).where(
                    Employee.role == Role.employee,
                    Employee.active == True,  # noqa: E712
                    Employee.is_demo == demo,
                )
            )
        )
        .scalars()
        .all()
    )


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


async def _live_staff(db: AsyncSession, *, demo: bool = False) -> list[LiveEmployeeOut]:
    emps = (
        await db.execute(
            select(Employee).where(Employee.active == True, Employee.is_demo == demo)  # noqa: E712
        )
    ).scalars().all()
    staff = [e for e in emps if e.role == Role.employee]
    day_clicks: dict[str, int] = defaultdict(int)
    day_keys: dict[str, int] = defaultdict(int)
    if staff and not demo:
        today = today_pk()
        start, end = day_bounds_utc(datetime(today.year, today.month, today.day))
        ids = [e.id for e in staff]
        buckets = (
            await db.execute(
                select(ActivityBucket).where(
                    ActivityBucket.employee_id.in_(ids),
                    ActivityBucket.bucket_start >= start,
                    ActivityBucket.bucket_start < end,
                )
            )
        ).scalars().all()
        for b in buckets:
            day_clicks[b.employee_id] += int(b.mouse_clicks or 0)
            day_keys[b.employee_id] += int(b.key_presses or 0)

    out: list[LiveEmployeeOut] = []
    for emp in staff:
        if demo:
            out.append(
                LiveEmployeeOut(
                    employee_id=emp.id,
                    code=emp.code,
                    full_name=emp.full_name,
                    status="offline",
                    last_window="Demo sample (no live PC)",
                    last_seen_at=None,
                    last_clicks_delta=0,
                    last_keys_delta=0,
                    day_clicks=0,
                    day_keys=0,
                    idle_seconds=0,
                    last_screenshot_url=None,
                )
            )
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
                day_clicks=int(day_clicks.get(emp.id) or 0),
                day_keys=int(day_keys.get(emp.id) or 0),
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
        if clicks or keys or day_shots:
            first = first_work_at(buckets=day_buckets, windows=day_windows, screenshots=day_shots)
            net, _ = inferred_work_session(
                first_at=first, last_at=work_at, idle_seconds=idle_sec
            )
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
    user: Annotated[Employee, Depends(require_office_or_demo)],
) -> list[LiveEmployeeOut]:
    return await _live_staff(db, demo=wants_demo_rows(user))


@router.get("/dashboard", response_model=DashboardOut)
async def dashboard_summary(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Employee, Depends(require_office_or_demo)],
) -> DashboardOut:
    demo = wants_demo_rows(user)
    live = await _live_staff(db, demo=demo)
    staff_count = len(live)
    live_now = sum(1 for r in live if r.status == "working")
    break_idle = sum(1 for r in live if r.status in ("break", "idle"))
    offline = sum(1 for r in live if r.status == "offline" or not r.status)

    projects = list(
        (await db.execute(select(Project).where(Project.is_demo == demo))).scalars().all()  # noqa: E712
    )
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
    if is_finance(user) and not demo:
        invs = list(
            (
                await db.execute(
                    select(Invoice)
                    .options(selectinload(Invoice.client))
                    .where(Invoice.is_demo == False)  # noqa: E712
                )
            ).scalars().all()
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

    partner_shares: DashPartnerShares | None = None
    if is_partner(user) and not demo:
        raw = await compute_partner_shares(db, year=today.year, month=today.month)
        partner_shares = DashPartnerShares(
            year=raw["year"],
            month=raw["month"],
            currency=raw["currency"],
            display_currency=raw.get("display_currency", "PKR"),
            usd_pkr_rate=raw["usd_pkr_rate"],
            rate_date=raw.get("rate_date"),
            rate_note=raw.get("rate_note", ""),
            partner_a_name=raw["partner_a_name"],
            partner_b_name=raw["partner_b_name"],
            paid_invoices_usd=raw["paid_invoices_usd"],
            paid_invoices_pkr=raw["paid_invoices_pkr"],
            paid_invoice_count=raw["paid_invoice_count"],
            expenses_pkr=raw["expenses_pkr"],
            expenses_usd=raw["expenses_usd"],
            expense_count=raw["expense_count"],
            net_usd=raw["net_usd"],
            net_pkr=raw["net_pkr"],
            faisal_share_usd=raw["faisal_share_usd"],
            faisal_share_pkr=raw["faisal_share_pkr"],
            asad_share_usd=raw["asad_share_usd"],
            asad_share_pkr=raw["asad_share_pkr"],
            split_percent=raw["split_percent"],
        )

    generated = now_pk().strftime("%H:%M")
    spark = [this_totals[d] for d in this_days]

    today_s = today.isoformat()
    progress_rows = list(
        (
            await db.execute(
                select(ProjectProgress)
                .options(
                    selectinload(ProjectProgress.employee),
                    selectinload(ProjectProgress.project),
                )
                .where(ProjectProgress.work_date == today_s)
                .order_by(ProjectProgress.created_at.desc())
            )
        )
        .scalars()
        .all()
    )
    progress_today: list[DashProgressRow] = []
    for row in progress_rows:
        proj = row.project
        if proj and bool(getattr(proj, "is_demo", False)) != demo:
            continue
        emp = row.employee
        progress_today.append(
            DashProgressRow(
                id=row.id,
                project_id=row.project_id,
                project_code=(proj.code if proj else "") or "",
                project_name=(proj.name if proj else "") or "—",
                employee_name=(emp.full_name if emp else "") or "—",
                percent=float(row.percent or 0),
                note=(row.note or "").strip(),
                work_date=row.work_date or today_s,
            )
        )
        if len(progress_today) >= 20:
            break

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
        progress_today=progress_today,
        finance=finance,
        partner_shares=partner_shares,
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
    emp = (
        await db.execute(select(Employee).where(Employee.id == employee_id))
    ).scalar_one_or_none()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
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
    if not sessions and (clicks or keys or shots):
        first = first_work_at(buckets=list(buckets), windows=list(windows), screenshots=list(shots))
        net, sessions = inferred_work_session(
            first_at=first, last_at=work_at, idle_seconds=idle_sec
        )
    return DaySummaryOut(
        employee_id=employee_id,
        date=date,
        employee_code=emp.code or "",
        employee_full_name=emp.full_name or "",
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
    if not sessions and (
        sum(b.mouse_clicks for b in buckets)
        or sum(b.key_presses for b in buckets)
        or shots
    ):
        net, sessions = inferred_work_session(
            first_at=first_at,
            last_at=work_at,
            idle_seconds=sum(b.idle_seconds for b in buckets),
        )
        overview_note = "No Sign In recorded — hours estimated from activity/screenshots"
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


@router.get("/me/attendance", response_model=MeAttendanceOut)
async def my_attendance(
    year: int,
    month: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Employee, Depends(get_current_user)],
) -> MeAttendanceOut:
    """Employee (or manager viewing self): month attendance for the signed-in user only."""
    reject_future_month(year, month)
    if user.role not in (Role.employee, Role.admin, Role.manager, Role.hr):
        raise HTTPException(status_code=403, detail="Attendance view not available for this role")
    emp_id = user.id
    # Build PKT calendar days in month
    first = date(year, month, 1)
    if month == 12:
        next_first = date(year + 1, 1, 1)
    else:
        next_first = date(year, month + 1, 1)
    days_list: list[date] = []
    d = first
    while d < next_first:
        days_list.append(d)
        d += timedelta(days=1)

    hours_map = await _hours_by_day(db, [emp_id], days_list)
    by_day = hours_map.get(emp_id) or {}
    start, _ = day_bounds_utc(datetime(year, month, 1))
    if month == 12:
        end, _ = day_bounds_utc(datetime(year + 1, 1, 1))
    else:
        end, _ = day_bounds_utc(datetime(year, month + 1, 1))
    sessions = await _sessions_capped(db, emp_id, start, end)
    brk = sum(s["break_minutes"] for s in sessions) / 60.0
    day_rows: list[MeAttendanceDay] = []
    net_total = 0.0
    present_n = 0
    for day in days_list:
        h = float(by_day.get(day) or 0)
        present = h > 0.01
        if present:
            present_n += 1
            net_total += h
        day_rows.append(
            MeAttendanceDay(
                date=day.isoformat(),
                label=day.strftime("%a %d"),
                net_hours=round(h, 2),
                present=present,
            )
        )
    return MeAttendanceOut(
        employee_id=emp_id,
        employee_code=user.code or "",
        employee_full_name=user.full_name or "",
        year=year,
        month=month,
        days_present=present_n,
        net_hours=round(net_total, 2),
        break_hours=round(brk, 2),
        days=day_rows,
    )


@router.get("/me/monthly.pdf")
async def my_monthly_pdf(
    year: int,
    month: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Employee, Depends(get_current_user)],
    inline: bool = False,
) -> FileResponse:
    """Personal monthly report — summary + every day (employee self-service)."""
    reject_future_month(year, month)
    if user.role not in (Role.employee, Role.admin, Role.manager, Role.hr):
        raise HTTPException(status_code=403, detail="Monthly PDF not available for this role")
    first = date(year, month, 1)
    if month == 12:
        next_first = date(year + 1, 1, 1)
    else:
        next_first = date(year, month + 1, 1)
    days_list: list[date] = []
    d = first
    while d < next_first:
        days_list.append(d)
        d += timedelta(days=1)
    hours_map = await _hours_by_day(db, [user.id], days_list)
    by_day = hours_map.get(user.id) or {}
    day_rows = [
        {"date": day.isoformat(), "net_hours": float(by_day.get(day) or 0), "present": float(by_day.get(day) or 0) > 0.01}
        for day in days_list
    ]
    code_safe = (user.code or "me").replace("/", "-")
    out_path = settings.data_path / "reports" / f"monthly_{code_safe}_{year}_{month:02d}.pdf"
    build_personal_monthly_pdf(
        out_path,
        year=year,
        month=month,
        employee_code=user.code or "",
        employee_name=user.full_name or "",
        day_rows=day_rows,
        overtime_hours_per_day=float(settings.overtime_hours_per_day),
    )
    disposition = "inline" if inline else "attachment"
    fname = f"monthly_{code_safe}_{year}_{month:02d}.pdf"
    return FileResponse(
        out_path,
        media_type="application/pdf",
        filename=fname,
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "Content-Disposition": f'{disposition}; filename="{fname}"',
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
