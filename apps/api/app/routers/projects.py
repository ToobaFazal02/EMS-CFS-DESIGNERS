import json
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import (
    get_current_user,
    is_demo_user,
    is_finance,
    is_manager,
    require_finance,
    require_office_or_demo,
)
from app.db import get_db
from app.models import AuditLog, Client, Employee, Project, ProjectPhase, Role, WorkState
from app.schemas import ClientIn, ClientOut, ProjectIn, ProjectOut
from app.services.data_scope import wants_demo_rows
from app.services.payments import gate_audience, gate_error, gate_status, normalize_currency, paid_amount

router = APIRouter(prefix="/api/v1", tags=["projects"])

PHASES = [p.value for p in ProjectPhase]
STATES = [s.value for s in WorkState]


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
    if body.storeys is not None and body.storeys < 0:
        raise HTTPException(status_code=400, detail="Storeys cannot be negative.")
    return name


def _client_out(c: Client, *, hide_private: bool) -> ClientOut:
    """HR/demo: name + location only — no phone/notes (may hold commercial secrets)."""
    return ClientOut(
        id=c.id,
        name=c.name,
        location=c.location or "",
        phone="" if hide_private else (c.phone or ""),
        notes="" if hide_private else (c.notes or ""),
        active=c.active,
    )


def _assert_row_scope(user: Employee, *, is_demo_row: bool) -> None:
    if wants_demo_rows(user) != bool(is_demo_row):
        raise HTTPException(status_code=404, detail="Not found")


def _project_out(p: Project, *, hide_money: bool = False) -> ProjectOut:
    client = p.client
    assignee = p.assignee
    paid = paid_amount(p)
    if hide_money:
        # Staff see ops fields only — never payment wording in comments
        safe_comments = p.comments or ""
        low = safe_comments.lower()
        if any(w in low for w in ("paid", "deposit", "invoice", "$", "payment", "advance", "balance")):
            safe_comments = ""
        return ProjectOut(
            id=p.id,
            name=p.name,
            client_id=p.client_id,
            client_name=client.name if client else "",
            client_location=client.location if client else "",
            work_scope=p.work_scope or "",
            assignee_id=p.assignee_id,
            assignee_name=assignee.full_name if assignee else "",
            area_sqft=p.area_sqft,
            storeys=p.storeys,
            phase=p.phase,
            work_state=p.work_state,
            comments=safe_comments,
            due_at=p.due_at,
            target_at=p.target_at,
            created_at=p.created_at,
            contract_value=0,
            deposit_pct=0,
            currency="",
            paid_amount=0,
            gate="ok",
        )
    return ProjectOut(
        id=p.id,
        name=p.name,
        client_id=p.client_id,
        client_name=client.name if client else "",
        client_location=client.location if client else "",
        work_scope=p.work_scope or "",
        assignee_id=p.assignee_id,
        assignee_name=assignee.full_name if assignee else "",
        area_sqft=p.area_sqft,
        storeys=p.storeys,
        phase=p.phase,
        work_state=p.work_state,
        comments=p.comments or "",
        due_at=p.due_at,
        target_at=p.target_at,
        created_at=p.created_at,
        contract_value=float(p.contract_value or 0),
        deposit_pct=float(p.deposit_pct or 50),
        currency=p.currency or "USD",
        paid_amount=paid,
        gate=gate_status(p),
    )


async def _load_project(db: AsyncSession, project_id: str) -> Project | None:
    return (
        await db.execute(
            select(Project)
            .options(
                selectinload(Project.client),
                selectinload(Project.assignee),
                selectinload(Project.invoices),
            )
            .where(Project.id == project_id)
        )
    ).scalar_one_or_none()


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
    }


@router.get("/clients", response_model=list[ClientOut])
async def list_clients(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Employee, Depends(require_office_or_demo)],
) -> list[ClientOut]:
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
    return [_client_out(c, hide_private=hide) for c in rows]


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
    phone = (body.phone or "").strip()[:40] if is_finance(user) else ""
    notes = (body.notes or "") if is_finance(user) else ""
    c = Client(
        name=name,
        location=location,
        phone=phone,
        notes=notes,
        is_demo=wants_demo_rows(user),
    )
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return _client_out(c, hide_private=not is_finance(user))


@router.get("/projects", response_model=list[ProjectOut])
async def list_projects(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Employee, Depends(get_current_user)],
) -> list[ProjectOut]:
    demo = wants_demo_rows(user)
    q = (
        select(Project)
        .options(
            selectinload(Project.client),
            selectinload(Project.assignee),
            selectinload(Project.invoices),
        )
        .where(Project.is_demo == demo)
        .order_by(Project.updated_at.desc())
    )
    if not is_manager(user) and not is_demo_user(user):
        q = q.where(Project.assignee_id == user.id)
    rows = list((await db.execute(q)).scalars().all())
    if user.role == Role.hr:
        rows = [p for p in rows if "SAMPLE" not in (p.name or "").upper() and "DEMO —" not in (p.name or "").upper()]
    hide = not is_finance(user)
    return [_project_out(p, hide_money=hide) for p in rows]


@router.post("/projects", response_model=ProjectOut)
async def create_project(
    body: ProjectIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Employee, Depends(require_office_or_demo)],
) -> ProjectOut:
    name = _validate_project_fields(body, require_contract=is_finance(user))
    phase = body.phase if body.phase in PHASES else ProjectPhase.intake.value
    state = body.work_state if body.work_state in STATES else WorkState.working.value
    demo = wants_demo_rows(user)
    if body.client_id:
        c = await db.get(Client, body.client_id)
        if not c or bool(c.is_demo) != demo:
            raise HTTPException(status_code=400, detail="Client not found")
    if body.assignee_id:
        emp = await db.get(Employee, body.assignee_id)
        if not emp or bool(getattr(emp, "is_demo", False)) != demo:
            raise HTTPException(status_code=400, detail="Assignee not found")
    if is_finance(user):
        value = float(body.contract_value or 0)
        deposit_pct = float(body.deposit_pct or 50)
        try:
            currency = normalize_currency(body.currency)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid currency code (use ISO 4217, e.g. USD, AUD, PKR)")
    else:
        # HR / demo: project ops without client $ fields
        value = 0.0
        deposit_pct = 50.0
        currency = "USD"
        body.override_gate = False
    # New jobs have $0 paid — refuse non-intake / release start unless override
    if value > 0 and not body.override_gate:
        aud = gate_audience(is_finance(user))
        deposit = value * (deposit_pct / 100.0)
        if phase != ProjectPhase.intake.value and deposit > 0:
            raise HTTPException(status_code=409, detail=gate_error("need_deposit", audience=aud))
        if phase in (
            ProjectPhase.stamped_drawings.value,
            ProjectPhase.field_files.value,
            ProjectPhase.run_files.value,
        ):
            raise HTTPException(status_code=409, detail=gate_error("need_final", audience=aud))
    p = Project(
        name=name,
        client_id=body.client_id,
        work_scope=(body.work_scope or "").strip(),
        assignee_id=body.assignee_id or None,
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
    db.add(p)
    await db.commit()
    loaded = await _load_project(db, p.id)
    assert loaded
    return _project_out(loaded, hide_money=not is_finance(user))


@router.patch("/projects/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: str,
    body: ProjectIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Employee, Depends(require_office_or_demo)],
) -> ProjectOut:
    p = await _load_project(db, project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    _assert_row_scope(user, is_demo_row=bool(p.is_demo))
    name = _validate_project_fields(body, require_contract=is_finance(user))
    if body.phase not in PHASES:
        raise HTTPException(status_code=400, detail="Invalid phase")
    if body.work_state not in STATES:
        raise HTTPException(status_code=400, detail="Invalid status")
    demo = wants_demo_rows(user)
    if body.client_id:
        c = await db.get(Client, body.client_id)
        if not c or bool(c.is_demo) != demo:
            raise HTTPException(status_code=400, detail="Client not found")
    if body.assignee_id:
        emp = await db.get(Employee, body.assignee_id)
        if not emp or bool(getattr(emp, "is_demo", False)) != demo:
            raise HTTPException(status_code=400, detail="Assignee not found")

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

    code = gate_status(p, new_phase=body.phase)
    allow = body.override_gate and is_finance(user)
    if code != "ok" and not allow:
        raise HTTPException(
            status_code=409,
            detail=gate_error(code, audience=gate_audience(is_finance(user))),
        )
    if allow and code != "ok":
        db.add(
            AuditLog(
                actor_id=user.id,
                action="payment_gate_override",
                entity="project",
                payload_json=json.dumps({"project_id": p.id, "phase": body.phase, "reason": (body.override_reason or "")[:200]}),
            )
        )

    p.name = name
    p.client_id = body.client_id
    p.work_scope = (body.work_scope or "").strip()
    p.assignee_id = body.assignee_id or None
    p.area_sqft = body.area_sqft
    p.storeys = body.storeys
    p.phase = body.phase
    p.work_state = body.work_state
    p.comments = (body.comments or "").strip()
    p.due_at = body.due_at
    p.target_at = body.target_at
    p.updated_at = datetime.utcnow()
    await db.commit()
    loaded = await _load_project(db, project_id)
    assert loaded
    return _project_out(loaded, hide_money=not is_finance(user))


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
    await db.commit()
    return {"ok": True, "id": project_id}
