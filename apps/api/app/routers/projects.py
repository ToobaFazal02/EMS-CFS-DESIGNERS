from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import get_current_user, is_manager, require_manager
from app.db import get_db
from app.models import AuditLog, Client, Employee, Project, ProjectPhase, Role, WorkState
from app.schemas import ClientIn, ClientOut, ProjectIn, ProjectOut
from app.services.payments import gate_error, gate_status, normalize_currency, paid_amount

router = APIRouter(prefix="/api/v1", tags=["projects"])

PHASES = [p.value for p in ProjectPhase]
STATES = [s.value for s in WorkState]


def _clean_project_name(raw: str | None) -> str:
    return " ".join((raw or "").split()).strip()


def _validate_project_fields(body: ProjectIn) -> str:
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
    if value <= 0:
        raise HTTPException(
            status_code=400,
            detail="Contract value is required (must be greater than 0). Without it, the 50% payment gate stays off.",
        )
    if body.area_sqft is not None and body.area_sqft < 0:
        raise HTTPException(status_code=400, detail="Area (sq.ft) cannot be negative.")
    if body.storeys is not None and body.storeys < 0:
        raise HTTPException(status_code=400, detail="Storeys cannot be negative.")
    return name


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
    _: Annotated[Employee, Depends(require_manager)],
) -> list[ClientOut]:
    rows = (await db.execute(select(Client).where(Client.active == True).order_by(Client.name))).scalars().all()  # noqa: E712
    return [ClientOut(id=c.id, name=c.name, location=c.location or "", notes=c.notes or "", active=c.active) for c in rows]


@router.post("/clients", response_model=ClientOut)
async def create_client(
    body: ClientIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Employee, Depends(require_manager)],
) -> ClientOut:
    name = (body.name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Client name is required")
    if len(name) < 2:
        raise HTTPException(status_code=400, detail="Client name is too short")
    location = (body.location or "").strip()
    if not location:
        raise HTTPException(status_code=400, detail="Client location is required (e.g. USA, AUS)")
    c = Client(name=name, location=location, notes=body.notes or "")
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return ClientOut(id=c.id, name=c.name, location=c.location, notes=c.notes, active=c.active)


@router.get("/projects", response_model=list[ProjectOut])
async def list_projects(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Employee, Depends(get_current_user)],
) -> list[ProjectOut]:
    q = (
        select(Project)
        .options(
            selectinload(Project.client),
            selectinload(Project.assignee),
            selectinload(Project.invoices),
        )
        .order_by(Project.updated_at.desc())
    )
    if not is_manager(user):
        q = q.where(Project.assignee_id == user.id)
    rows = (await db.execute(q)).scalars().all()
    hide = not is_manager(user)
    return [_project_out(p, hide_money=hide) for p in rows]


@router.post("/projects", response_model=ProjectOut)
async def create_project(
    body: ProjectIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Employee, Depends(require_manager)],
) -> ProjectOut:
    name = _validate_project_fields(body)
    phase = body.phase if body.phase in PHASES else ProjectPhase.intake.value
    state = body.work_state if body.work_state in STATES else WorkState.working.value
    if body.client_id:
        c = await db.get(Client, body.client_id)
        if not c:
            raise HTTPException(status_code=400, detail="Client not found")
    if body.assignee_id:
        emp = await db.get(Employee, body.assignee_id)
        if not emp or emp.role != Role.employee:
            raise HTTPException(status_code=400, detail="Assignee not found")
    value = float(body.contract_value or 0)
    deposit_pct = float(body.deposit_pct or 50)
    try:
        currency = normalize_currency(body.currency)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid currency code (use ISO 4217, e.g. USD, AUD, PKR)")
    # New jobs have $0 paid — refuse non-intake / release start unless override
    if value > 0 and not body.override_gate:
        deposit = value * (deposit_pct / 100.0)
        if phase != ProjectPhase.intake.value and deposit > 0:
            raise HTTPException(status_code=409, detail=gate_error("need_deposit"))
        if phase in (
            ProjectPhase.stamped_drawings.value,
            ProjectPhase.field_files.value,
            ProjectPhase.run_files.value,
        ):
            raise HTTPException(status_code=409, detail=gate_error("need_final"))
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
    )
    if body.override_gate and phase != ProjectPhase.intake.value and value > 0:
        db.add(
            AuditLog(
                actor_id=user.id,
                action="payment_gate_override",
                entity="project",
                payload_json=(
                    f'{{"phase":"{phase}","reason":"{(body.override_reason or "create")[:200]}"}}'
                ),
            )
        )
    db.add(p)
    await db.commit()
    loaded = await _load_project(db, p.id)
    assert loaded
    return _project_out(loaded)


@router.patch("/projects/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: str,
    body: ProjectIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Employee, Depends(require_manager)],
) -> ProjectOut:
    p = await _load_project(db, project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    name = _validate_project_fields(body)
    if body.phase not in PHASES:
        raise HTTPException(status_code=400, detail="Invalid phase")
    if body.work_state not in STATES:
        raise HTTPException(status_code=400, detail="Invalid status")
    if body.client_id:
        c = await db.get(Client, body.client_id)
        if not c:
            raise HTTPException(status_code=400, detail="Client not found")
    if body.assignee_id:
        emp = await db.get(Employee, body.assignee_id)
        if not emp or emp.role != Role.employee:
            raise HTTPException(status_code=400, detail="Assignee not found")

    p.contract_value = float(body.contract_value or 0)
    p.deposit_pct = float(body.deposit_pct or 50)
    try:
        p.currency = normalize_currency(body.currency)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid currency code (use ISO 4217, e.g. USD, AUD, PKR)")
    await db.flush()

    code = gate_status(p, new_phase=body.phase)
    allow = body.override_gate and user.role in (Role.admin, Role.manager)
    if code != "ok" and not allow:
        raise HTTPException(status_code=409, detail=gate_error(code))
    if allow and code != "ok":
        db.add(
            AuditLog(
                actor_id=user.id,
                action="payment_gate_override",
                entity="project",
                payload_json=(
                    f'{{"project_id":"{p.id}","phase":"{body.phase}",'
                    f'"reason":"{(body.override_reason or "")[:200]}"}}'
                ),
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
    return _project_out(loaded)


@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Employee, Depends(require_manager)],
) -> dict:
    """Admin/manager only. Detaches invoices (keeps payment history), then removes project."""
    p = await _load_project(db, project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    name = p.name
    for inv in list(p.invoices or []):
        inv.project_id = None
    await db.delete(p)
    db.add(
        AuditLog(
            actor_id=user.id,
            action="project_delete",
            entity="project",
            payload_json=f'{{"project_id":"{project_id}","name":"{name[:120]}"}}',
        )
    )
    await db.commit()
    return {"ok": True, "id": project_id}
