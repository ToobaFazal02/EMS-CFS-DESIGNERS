import json
from datetime import datetime
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, exists, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.services.notifications import notify_office
from app.auth import (
    get_current_user,
    is_demo_user,
    is_finance,
    is_manager,
    require_finance,
    require_office_or_demo,
)
from app.db import get_db
from app.models import (
    AssigneeRole,
    AuditLog,
    Client,
    ClientInvoiceStatus,
    Employee,
    Project,
    ProjectAssignee,
    ProjectPhase,
    ProjectProgress,
    Role,
    WorkState,
)
from app.schemas import (
    ClientIn,
    ClientOut,
    ProjectAssigneeOut,
    ProjectIn,
    ProjectOut,
    ProjectProgressIn,
    ProjectProgressOut,
)
from app.services.data_scope import wants_demo_rows
from app.services.payments import (
    RELEASE_PHASES,
    gate_audience,
    gate_blocks_hard,
    gate_error,
    gate_status,
    normalize_currency,
    paid_amount,
)
from app.services.project_codes import (
    SCOPE_LABELS,
    SCOPE_VALUES,
    build_project_code,
    normalize_initial,
    normalize_scope,
    resolve_role_ids,
)

router = APIRouter(prefix="/api/v1", tags=["projects"])

PHASES = [p.value for p in ProjectPhase]
STATES = [s.value for s in WorkState]
INVOICE_STATUSES = {s.value for s in ClientInvoiceStatus}
PKT = ZoneInfo("Asia/Karachi")


def _clean_project_name(raw: str | None) -> str:
    return " ".join((raw or "").split()).strip()


def _validate_project_fields(body: ProjectIn, *, require_contract: bool) -> str:
    """Return cleaned name or raise 400. Client is required for a real Design Queue card."""
    name = _clean_project_name(body.name)
    if len(name) < 4:
        raise HTTPException(
            status_code=400,
            detail="Project name must be at least 4 characters (e.g. LOT 12 Main St).",
        )
    letters = sum(1 for c in name if c.isalpha())
    if letters < 2:
        raise HTTPException(status_code=400, detail="Project name must include letters.")
    # Block keyboard-smash / placeholder: need a space, digit, hyphen, or a longer real title
    if " " not in name and "-" not in name and not any(c.isdigit() for c in name) and len(name) < 10:
        raise HTTPException(
            status_code=400,
            detail="Use a clear job title (include address, lot #, or full building name).",
        )
    if not (body.client_id or "").strip():
        raise HTTPException(status_code=400, detail="Client is required. Add a client first, then select it.")
    deposit = float(body.deposit_pct if body.deposit_pct is not None else 50)
    if deposit < 0 or deposit > 100:
        raise HTTPException(status_code=400, detail="Deposit % must be between 0 and 100.")
    value = float(body.contract_value or 0)
    if value < 0:
        raise HTTPException(status_code=400, detail="Contract value cannot be negative.")
    if require_contract and value <= 0:
        raise HTTPException(
            status_code=400,
            detail="Contract value is required (must be greater than 0). Without it, the 50% payment gate stays off.",
        )
    if body.area_sqft is not None and body.area_sqft < 0:
        raise HTTPException(status_code=400, detail="Area (sq.ft) cannot be negative.")
    if body.area_sqft is not None and body.area_sqft > 5_000_000:
        raise HTTPException(status_code=400, detail="Area (sq.ft) looks too large — check the number.")
    if body.storeys is not None and body.storeys < 0:
        raise HTTPException(status_code=400, detail="Storeys cannot be negative.")
    if body.storeys is not None and body.storeys > 200:
        raise HTTPException(status_code=400, detail="Storeys must be 200 or fewer.")
    return name


def _normalize_invoice_status(raw: str | None) -> str:
    s = (raw or ClientInvoiceStatus.none.value).strip().lower()
    if s not in INVOICE_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid invoice status")
    return s


def _client_display_name(c: Client, *, mask_name: bool) -> str:
    """Employees see initial + location only; office/finance see the real firm name."""
    if not mask_name:
        return c.name or ""
    ini = (c.initial or "").strip().upper()
    loc = (c.location or "").strip()
    if ini and loc:
        return f"[{ini}] · {loc}"
    if ini:
        return f"[{ini}]"
    return loc or "Client"


def _client_out(c: Client, *, hide_private: bool, mask_name: bool = False) -> ClientOut:
    """Non-finance: no phone/notes. Employees: masked display name (initial + location)."""
    return ClientOut(
        id=c.id,
        name=_client_display_name(c, mask_name=mask_name),
        location=c.location or "",
        phone="" if hide_private else (c.phone or ""),
        notes="" if hide_private else (c.notes or ""),
        initial=c.initial or "",
        invoice_status=c.invoice_status or ClientInvoiceStatus.none.value,
        active=c.active,
    )


def _mask_client_for(user: Employee) -> bool:
    return user.role == Role.employee


def _assert_row_scope(user: Employee, *, is_demo_row: bool) -> None:
    if wants_demo_rows(user) != bool(is_demo_row):
        raise HTTPException(status_code=404, detail="Not found")


def _assignee_outs(p: Project) -> list[ProjectAssigneeOut]:
    rows: list[ProjectAssigneeOut] = []
    for a in p.assignees or []:
        emp = a.employee
        rows.append(
            ProjectAssigneeOut(
                employee_id=a.employee_id,
                full_name=emp.full_name if emp else "",
                code=emp.code if emp else "",
                is_lead=bool(a.is_lead),
                role=(a.role or "") if hasattr(a, "role") else "",
            )
        )
    if rows:
        return rows
    # Legacy single assignee_id with no junction rows yet
    if p.assignee_id and p.assignee:
        return [
            ProjectAssigneeOut(
                employee_id=p.assignee_id,
                full_name=p.assignee.full_name or "",
                code=p.assignee.code or "",
                is_lead=True,
                role=AssigneeRole.detailer.value,
            )
        ]
    return []


def _roles_from_project(p: Project) -> tuple[str | None, str, str | None, str]:
    """Return detailer_id, detailer_name, engineer_id, engineer_name."""
    detailer_id: str | None = None
    detailer_name = ""
    engineer_id: str | None = None
    engineer_name = ""
    for a in p.assignees or []:
        emp = a.employee
        name = emp.full_name if emp else ""
        role = (getattr(a, "role", None) or "").strip().lower()
        if role == AssigneeRole.detailer.value or (not role and a.is_lead):
            detailer_id = a.employee_id
            detailer_name = name
        elif role == AssigneeRole.engineer.value:
            engineer_id = a.employee_id
            engineer_name = name
    if not detailer_id and p.assignee_id:
        detailer_id = p.assignee_id
        detailer_name = p.assignee.full_name if p.assignee else ""
    return detailer_id, detailer_name, engineer_id, engineer_name


def _latest_progress_pct(p: Project) -> float | None:
    rows = list(p.progress_rows or [])
    if not rows:
        return None
    today = datetime.now(PKT).strftime("%Y-%m-%d")
    today_rows = [r for r in rows if (r.work_date or "") == today]
    if today_rows:
        return max(float(r.percent or 0) for r in today_rows)
    best = max(rows, key=lambda r: (r.work_date or "", r.created_at or datetime.min))
    return float(best.percent or 0)


def _project_out(p: Project, *, hide_money: bool = False, mask_client: bool = False) -> ProjectOut:
    client = p.client
    assignee = p.assignee
    paid = paid_amount(p)
    assignees = _assignee_outs(p)
    detailer_id, detailer_name, engineer_id, engineer_name = _roles_from_project(p)
    client_initial = (client.initial if client else "") or ""
    code = p.code or ""
    progress = _latest_progress_pct(p)
    client_name = _client_display_name(client, mask_name=mask_client) if client else ""
    base_kwargs = dict(
        id=p.id,
        name=p.name,
        code=code,
        client_id=p.client_id,
        client_name=client_name,
        client_location=client.location if client else "",
        client_initial=client_initial,
        work_scope=p.work_scope or "",
        assignee_id=p.assignee_id or detailer_id,
        assignee_name=assignee.full_name if assignee else detailer_name,
        assignees=assignees,
        detailer_id=detailer_id,
        detailer_name=detailer_name,
        engineer_id=engineer_id,
        engineer_name=engineer_name,
        area_sqft=p.area_sqft,
        storeys=p.storeys,
        phase=p.phase,
        work_state=p.work_state,
        due_at=p.due_at,
        target_at=p.target_at,
        created_at=p.created_at,
        latest_progress_pct=progress,
    )
    if hide_money:
        # Staff see ops fields only — never payment wording in comments; keep soft gate badge
        safe_comments = p.comments or ""
        low = safe_comments.lower()
        if any(w in low for w in ("paid", "deposit", "invoice", "$", "payment", "advance", "balance")):
            safe_comments = ""
        return ProjectOut(
            **base_kwargs,
            comments=safe_comments,
            contract_value=0,
            deposit_pct=0,
            currency="",
            paid_amount=0,
            gate=gate_status(p),
        )
    return ProjectOut(
        **base_kwargs,
        comments=p.comments or "",
        contract_value=float(p.contract_value or 0),
        deposit_pct=float(p.deposit_pct or 50),
        currency=p.currency or "USD",
        paid_amount=paid,
        gate=gate_status(p),
    )


def _project_load_options():
    return (
        selectinload(Project.client),
        selectinload(Project.assignee),
        selectinload(Project.invoices),
        selectinload(Project.assignees).selectinload(ProjectAssignee.employee),
        selectinload(Project.progress_rows),
    )


async def _load_project(db: AsyncSession, project_id: str) -> Project | None:
    return (
        await db.execute(
            select(Project).options(*_project_load_options()).where(Project.id == project_id)
        )
    ).scalar_one_or_none()


def _user_on_project(p: Project, user_id: str) -> bool:
    if p.assignee_id == user_id:
        return True
    return any(a.employee_id == user_id for a in (p.assignees or []))


def _assert_project_access(user: Employee, p: Project) -> None:
    """Managers/demo see all in scope; staff only assignee membership."""
    if is_manager(user) or is_demo_user(user):
        return
    if _user_on_project(p, user.id):
        return
    raise HTTPException(status_code=403, detail="Not assigned to this project")


async def _validate_assignee_employees(
    db: AsyncSession, ids: list[str], *, demo: bool
) -> None:
    for eid in ids:
        emp = await db.get(Employee, eid)
        if not emp or not emp.active or bool(getattr(emp, "is_demo", False)) != demo:
            raise HTTPException(status_code=400, detail="Assignee not found")


async def _sync_role_assignees(
    db: AsyncSession,
    project: Project,
    *,
    detailer_id: str,
    engineer_id: str,
    demo: bool,
) -> None:
    """Replace Detailer + Engineer without touching unloaded relationship (avoids MissingGreenlet)."""
    await _validate_assignee_employees(db, [detailer_id, engineer_id], demo=demo)
    await db.execute(delete(ProjectAssignee).where(ProjectAssignee.project_id == project.id))
    await db.flush()
    project.assignee_id = detailer_id
    db.add(
        ProjectAssignee(
            project_id=project.id,
            employee_id=detailer_id,
            role=AssigneeRole.detailer.value,
            is_lead=True,
        )
    )
    db.add(
        ProjectAssignee(
            project_id=project.id,
            employee_id=engineer_id,
            role=AssigneeRole.engineer.value,
            is_lead=False,
        )
    )


def _require_roles(body: ProjectIn) -> tuple[str, str]:
    detailer_id, engineer_id = resolve_role_ids(
        detailer_id=body.detailer_id,
        engineer_id=body.engineer_id,
        assignee_id=body.assignee_id,
        assignee_ids=body.assignee_ids,
    )
    if not detailer_id:
        raise HTTPException(status_code=400, detail="Detailer is required")
    if not engineer_id:
        raise HTTPException(status_code=400, detail="Engineer is required")
    return detailer_id, engineer_id


def _friendly_save_error() -> HTTPException:
    return HTTPException(
        status_code=500,
        detail="Could not save project. Please try again. If this keeps happening, restart the API and refresh.",
    )


def _require_valid_scope(raw: str | None, *, existing: str = "") -> str:
    scope = normalize_scope(raw)
    if scope in SCOPE_VALUES:
        return scope
    # Legacy cards: allow keep-as-is when already a locked enum value
    if (existing or "") in SCOPE_VALUES and (not (raw or "").strip() or (raw or "").strip() == existing):
        return existing
    raise HTTPException(
        status_code=400,
        detail="Work scope must be Estimation, Detailing, or Detailing + Engineering",
    )


def _pkt_today() -> str:
    return datetime.now(PKT).strftime("%Y-%m-%d")


def _progress_out(row: ProjectProgress) -> ProjectProgressOut:
    emp = row.employee
    return ProjectProgressOut(
        id=row.id,
        employee_id=row.employee_id,
        employee_name=emp.full_name if emp else "",
        work_date=row.work_date,
        percent=float(row.percent or 0),
        note=row.note or "",
        created_at=row.created_at,
    )


@router.get("/project-phases")
async def project_phases(_: Annotated[Employee, Depends(get_current_user)]) -> dict:
    return {
        "phases": PHASES,
        "labels": {
            "intake": "Intake",
            "preliminary_design": "Preliminary Design",
            "preliminary_engineering": "Preliminary Engineering",
            "final_engineering": "Final Engineering",
            "stamped_drawings": "Stamped Drawings",
            "field_files": "Field Files",
            "run_files": "Run Files",
        },
        "states": STATES,
        "scopes": sorted(SCOPE_VALUES),
        "scope_labels": SCOPE_LABELS,
    }


@router.get("/clients", response_model=list[ClientOut])
async def list_clients(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Employee, Depends(get_current_user)],
) -> list[ClientOut]:
    """Any signed-in user can list active clients (staff need them to create projects)."""
    demo = wants_demo_rows(user)
    q = (
        select(Client)
        .where(Client.active == True, Client.is_demo == demo)  # noqa: E712
        .order_by(Client.name)
    )
    rows = (await db.execute(q)).scalars().all()
    # HR: never show training SAMPLE rows — only real CFS clients (+ what HR adds)
    if user.role == Role.hr:
        rows = [c for c in rows if "SAMPLE" not in (c.name or "").upper() and "(DEMO)" not in (c.name or "").upper()]
    hide = not is_finance(user)
    mask = _mask_client_for(user)
    return [_client_out(c, hide_private=hide, mask_name=mask) for c in rows]


@router.post("/clients", response_model=ClientOut)
async def create_client(
    body: ClientIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Employee, Depends(require_office_or_demo)],
) -> ClientOut:
    name = (body.name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Client name is required")
    if len(name) < 2:
        raise HTTPException(status_code=400, detail="Client name is too short")
    location = (body.location or "").strip()
    if not location:
        raise HTTPException(status_code=400, detail="Client location is required (e.g. USA, AUS)")
    if not (body.initial or "").strip():
        raise HTTPException(status_code=400, detail="Client initial is required (1–4 letters)")
    initial = normalize_initial(body.initial, fallback_name=name)
    if not initial:
        raise HTTPException(status_code=400, detail="Client initial is required (1–4 letters)")
    invoice_status = _normalize_invoice_status(body.invoice_status)
    phone = (body.phone or "").strip()[:40] if is_finance(user) else ""
    notes = (body.notes or "") if is_finance(user) else ""
    c = Client(
        name=name,
        location=location,
        phone=phone,
        notes=notes,
        initial=initial,
        invoice_status=invoice_status,
        is_demo=wants_demo_rows(user),
    )
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return _client_out(
        c,
        hide_private=not is_finance(user),
        mask_name=_mask_client_for(user),
    )


@router.patch("/clients/{client_id}", response_model=ClientOut)
async def patch_client(
    client_id: str,
    body: ClientIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Employee, Depends(require_office_or_demo)],
) -> ClientOut:
    c = await db.get(Client, client_id)
    if not c or not c.active:
        raise HTTPException(status_code=404, detail="Client not found")
    _assert_row_scope(user, is_demo_row=bool(c.is_demo))
    name = (body.name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Client name is required")
    if len(name) < 2:
        raise HTTPException(status_code=400, detail="Client name is too short")
    location = (body.location or "").strip()
    if not location:
        raise HTTPException(status_code=400, detail="Client location is required (e.g. USA, AUS)")
    if not (body.initial or "").strip():
        raise HTTPException(status_code=400, detail="Client initial is required (1–4 letters)")
    initial = normalize_initial(body.initial, fallback_name=name)
    invoice_status = _normalize_invoice_status(body.invoice_status)
    c.name = name
    c.location = location
    c.initial = initial
    c.invoice_status = invoice_status
    if is_finance(user):
        c.phone = (body.phone or "").strip()[:40]
        c.notes = body.notes or ""
    await db.commit()
    await db.refresh(c)
    return _client_out(
        c,
        hide_private=not is_finance(user),
        mask_name=_mask_client_for(user),
    )


@router.get("/projects", response_model=list[ProjectOut])
async def list_projects(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Employee, Depends(get_current_user)],
) -> list[ProjectOut]:
    demo = wants_demo_rows(user)
    q = (
        select(Project)
        .options(*_project_load_options())
        .where(Project.is_demo == demo)
        .order_by(Project.updated_at.desc())
    )
    if not is_manager(user) and not is_demo_user(user):
        on_team = exists().where(
            ProjectAssignee.project_id == Project.id,
            ProjectAssignee.employee_id == user.id,
        )
        q = q.where(or_(Project.assignee_id == user.id, on_team))
    rows = list((await db.execute(q)).scalars().all())
    if user.role == Role.hr:
        rows = [p for p in rows if "SAMPLE" not in (p.name or "").upper() and "DEMO —" not in (p.name or "").upper()]
    hide = not is_finance(user)
    mask = _mask_client_for(user)
    return [_project_out(p, hide_money=hide, mask_client=mask) for p in rows]


@router.post("/projects", response_model=ProjectOut)
async def create_project(
    body: ProjectIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Employee, Depends(get_current_user)],
) -> ProjectOut:
    """Staff (employee) + office/demo can create. Finance required for contract $ fields."""
    name = _validate_project_fields(body, require_contract=is_finance(user))
    scope = _require_valid_scope(body.work_scope)
    phase = body.phase if body.phase in PHASES else ProjectPhase.intake.value
    state = body.work_state if body.work_state in STATES else WorkState.working.value
    demo = wants_demo_rows(user)
    client = await db.get(Client, body.client_id)
    if not client or bool(client.is_demo) != demo or not client.active:
        raise HTTPException(status_code=400, detail="Client not found")
    detailer_id, engineer_id = _require_roles(body)
    code = build_project_code(client.initial or "", override=body.code or "")
    # Employees never override auto codes — ignore client-facing code internals
    if user.role == Role.employee:
        code = build_project_code(client.initial or "", override="")
    if is_finance(user):
        value = float(body.contract_value or 0)
        deposit_pct = float(body.deposit_pct or 50)
        try:
            currency = normalize_currency(body.currency)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid currency code (use ISO 4217, e.g. USD, AUD, PKR)")
    else:
        # Staff / HR / demo: project ops without client $ fields
        value = 0.0
        deposit_pct = 50.0
        currency = "USD"
        body.override_gate = False
    # Soft gate on create: only hard-block release phases without payment
    if value > 0 and not body.override_gate:
        aud = gate_audience(is_finance(user))
        deposit = value * (deposit_pct / 100.0)
        if phase in RELEASE_PHASES and deposit > 0:
            raise HTTPException(
                status_code=409,
                detail=gate_error("need_deposit", audience=aud, hard=True),
            )
        if phase in RELEASE_PHASES:
            raise HTTPException(
                status_code=409,
                detail=gate_error("need_final", audience=aud, hard=True),
            )
    p = Project(
        name=name,
        code=code,
        client_id=body.client_id,
        work_scope=scope,
        assignee_id=detailer_id,
        area_sqft=body.area_sqft,
        storeys=body.storeys,
        phase=phase,
        work_state=state,
        comments=(body.comments or "").strip(),
        due_at=body.due_at,
        target_at=body.target_at,
        contract_value=value,
        deposit_pct=deposit_pct,
        currency=currency,
        is_demo=demo,
    )
    if body.override_gate and phase != ProjectPhase.intake.value and value > 0:
        db.add(
            AuditLog(
                actor_id=user.id,
                action="payment_gate_override",
                entity="project",
                payload_json=json.dumps({"phase": phase, "reason": (body.override_reason or "create")[:200]}),
            )
        )
    try:
        db.add(p)
        await db.flush()
        await _sync_role_assignees(
            db, p, detailer_id=detailer_id, engineer_id=engineer_id, demo=demo
        )
        await db.commit()
    except HTTPException:
        raise
    except Exception:
        await db.rollback()
        raise _friendly_save_error()
    loaded = await _load_project(db, p.id)
    assert loaded
    return _project_out(
        loaded,
        hide_money=not is_finance(user),
        mask_client=_mask_client_for(user),
    )


@router.patch("/projects/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: str,
    body: ProjectIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Employee, Depends(get_current_user)],
) -> ProjectOut:
    p = await _load_project(db, project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    _assert_row_scope(user, is_demo_row=bool(p.is_demo))
    _assert_project_access(user, p)
    name = _validate_project_fields(body, require_contract=is_finance(user))
    scope = _require_valid_scope(body.work_scope, existing=p.work_scope or "")
    if body.phase not in PHASES:
        raise HTTPException(status_code=400, detail="Invalid phase")
    if body.work_state not in STATES:
        raise HTTPException(status_code=400, detail="Invalid status")
    demo = wants_demo_rows(user)
    client = await db.get(Client, body.client_id)
    if not client or bool(client.is_demo) != demo or not client.active:
        raise HTTPException(status_code=400, detail="Client not found")
    detailer_id, engineer_id = _require_roles(body)

    if is_finance(user):
        p.contract_value = float(body.contract_value or 0)
        p.deposit_pct = float(body.deposit_pct or 50)
        try:
            p.currency = normalize_currency(body.currency)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid currency code (use ISO 4217, e.g. USD, AUD, PKR)")
    else:
        body.override_gate = False
    await db.flush()

    gate_code = gate_status(p, new_phase=body.phase)
    allow = body.override_gate and is_finance(user)
    hard = gate_blocks_hard(gate_code, body.phase)
    aud = gate_audience(is_finance(user))
    if hard and not allow:
        raise HTTPException(
            status_code=409,
            detail=gate_error(gate_code, audience=aud, hard=True),
        )
    left_intake = (
        (p.phase or "") == ProjectPhase.intake.value
        and body.phase != ProjectPhase.intake.value
    )
    if gate_code == "need_deposit" and left_intake and not hard:
        db.add(
            AuditLog(
                actor_id=user.id,
                action="deposit_unpaid_phase_advance",
                entity="project",
                payload_json=json.dumps(
                    {
                        "project_id": p.id,
                        "from_phase": p.phase,
                        "to_phase": body.phase,
                        "note": "Soft gate: design work continued without Paid deposit",
                    }
                ),
            )
        )
        await notify_office(
            db,
            kind="warning",
            title="Deposit unpaid — phase advanced",
            body=(
                f"Project {(p.code or p.name or p.id)[:80]} left Intake without a Paid deposit "
                f"({p.phase} → {body.phase})."
            ),
            href="/projects",
            ref_key=f"deposit_unpaid:{p.id}:{body.phase}",
            payload={"project_id": p.id, "to_phase": body.phase},
        )
    if allow and hard:
        db.add(
            AuditLog(
                actor_id=user.id,
                action="payment_gate_override",
                entity="project",
                payload_json=json.dumps(
                    {"project_id": p.id, "phase": body.phase, "reason": (body.override_reason or "")[:200]}
                ),
            )
        )
        await notify_office(
            db,
            kind="alert",
            title="Payment gate override",
            body=(
                f"Hard payment gate overridden for {(p.code or p.name or p.id)[:80]} "
                f"at phase {body.phase}."
            ),
            href="/projects",
            ref_key=f"gate_override:{p.id}:{body.phase}:{datetime.utcnow().strftime('%Y%m%d%H')}",
            payload={"project_id": p.id, "phase": body.phase},
        )

    p.name = name
    if user.role == Role.employee:
        if not (p.code or "").strip():
            p.code = build_project_code(client.initial or "")
    elif (body.code or "").strip():
        p.code = build_project_code(client.initial or "", override=body.code)
    elif not (p.code or "").strip():
        p.code = build_project_code(client.initial or "")
    p.client_id = body.client_id
    p.work_scope = scope
    p.area_sqft = body.area_sqft
    p.storeys = body.storeys
    p.phase = body.phase
    p.work_state = body.work_state
    p.comments = (body.comments or "").strip()
    p.due_at = body.due_at
    p.target_at = body.target_at
    p.updated_at = datetime.utcnow()
    try:
        await _sync_role_assignees(
            db, p, detailer_id=detailer_id, engineer_id=engineer_id, demo=demo
        )
        await db.commit()
    except HTTPException:
        raise
    except Exception:
        await db.rollback()
        raise _friendly_save_error()
    loaded = await _load_project(db, project_id)
    assert loaded
    return _project_out(
        loaded,
        hide_money=not is_finance(user),
        mask_client=_mask_client_for(user),
    )


@router.get("/projects/{project_id}/progress", response_model=list[ProjectProgressOut])
async def list_project_progress(
    project_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Employee, Depends(get_current_user)],
) -> list[ProjectProgressOut]:
    p = await _load_project(db, project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    _assert_row_scope(user, is_demo_row=bool(p.is_demo))
    _assert_project_access(user, p)
    q = (
        select(ProjectProgress)
        .options(selectinload(ProjectProgress.employee))
        .where(ProjectProgress.project_id == project_id)
        .order_by(ProjectProgress.work_date.desc(), ProjectProgress.created_at.desc())
    )
    rows = (await db.execute(q)).scalars().all()
    return [_progress_out(r) for r in rows]


@router.post("/projects/{project_id}/progress", response_model=ProjectProgressOut)
async def post_project_progress(
    project_id: str,
    body: ProjectProgressIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Employee, Depends(get_current_user)],
) -> ProjectProgressOut:
    p = await _load_project(db, project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    _assert_row_scope(user, is_demo_row=bool(p.is_demo))
    _assert_project_access(user, p)
    pct = float(body.percent)
    if pct < 0 or pct > 100:
        raise HTTPException(status_code=400, detail="Percent must be between 0 and 100")
    work_date = (body.work_date or "").strip() or _pkt_today()
    if len(work_date) != 10 or work_date[4] != "-" or work_date[7] != "-":
        raise HTTPException(status_code=400, detail="work_date must be YYYY-MM-DD")
    emp_id = (body.employee_id or "").strip() or user.id
    if emp_id != user.id and not (is_manager(user) or is_demo_user(user)):
        raise HTTPException(status_code=403, detail="Cannot log progress for another person")
    demo = wants_demo_rows(user)
    emp = await db.get(Employee, emp_id)
    if not emp or not emp.active or bool(getattr(emp, "is_demo", False)) != demo:
        raise HTTPException(status_code=400, detail="Employee not found")
    # Upsert same day + employee
    existing = (
        await db.execute(
            select(ProjectProgress)
            .options(selectinload(ProjectProgress.employee))
            .where(
                ProjectProgress.project_id == project_id,
                ProjectProgress.employee_id == emp_id,
                ProjectProgress.work_date == work_date,
            )
        )
    ).scalar_one_or_none()
    note = (body.note or "").strip()[:500]
    if existing:
        existing.percent = pct
        existing.note = note
        row = existing
    else:
        row = ProjectProgress(
            project_id=project_id,
            employee_id=emp_id,
            work_date=work_date,
            percent=pct,
            note=note,
        )
        db.add(row)
    p.updated_at = datetime.utcnow()
    if user.role == Role.employee:
        await notify_office(
            db,
            kind="info",
            title="Staff progress update",
            body=f"{(emp.full_name or 'Staff')} logged {pct:.0f}% on {(p.code or p.name or '')[:60]}",
            href="/projects",
            ref_key=f"progress:{project_id}:{emp_id}:{work_date}",
            payload={"project_id": project_id, "percent": pct, "employee_id": emp_id},
        )
    await db.commit()
    await db.refresh(row)
    loaded = (
        await db.execute(
            select(ProjectProgress)
            .options(selectinload(ProjectProgress.employee))
            .where(ProjectProgress.id == row.id)
        )
    ).scalar_one()
    return _progress_out(loaded)


@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Employee, Depends(require_finance)],
) -> dict:
    """Admin/manager only — HR cannot delete (protects invoice linkage / history)."""
    p = await _load_project(db, project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    if p.is_demo:
        raise HTTPException(status_code=403, detail="Use demo tools only inside the demo catalog")
    name = p.name
    for inv in list(p.invoices or []):
        inv.project_id = None
    await db.delete(p)
    db.add(
        AuditLog(
            actor_id=user.id,
            action="project_delete",
            entity="project",
            payload_json=json.dumps({"project_id": project_id, "name": name[:120]}),
        )
    )
    await notify_office(
        db,
        kind="alert",
        title="Project deleted",
        body=f"Project “{name[:100]}” was deleted.",
        href="/projects",
        ref_key=f"project_delete:{project_id}",
        payload={"project_id": project_id},
    )
    await db.commit()
    return {"ok": True, "id": project_id}
