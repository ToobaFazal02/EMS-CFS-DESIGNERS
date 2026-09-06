import secrets
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import (
    create_access_token,
    create_device_token,
    get_current_user,
    hash_password,
    hash_token,
    require_manager,
    require_office_or_demo,
    verify_password,
)
from app.db import get_db
from app.models import Device, Employee, Role
from app.rate_limit import client_ip, hit
from app.schemas import (
    ChangeDisplayNameIn,
    ChangeEmailIn,
    ChangePasswordIn,
    EmployeeCreate,
    EmployeeCredentialsIn,
    EmployeeOut,
    EmployeeUpdate,
    EnrollCompleteIn,
    EnrollCompleteOut,
    EnrollStartOut,
    LoginIn,
    TokenOut,
)

router = APIRouter(prefix="/api/v1", tags=["auth"])


async def employee_to_out(db: AsyncSession, emp: Employee) -> EmployeeOut:
    devices = list(
        (
            await db.execute(
                select(Device)
                .where(Device.employee_id == emp.id, Device.enrolled_at.is_not(None))
                .order_by(Device.enrolled_at.desc())
            )
        ).scalars().all()
    )
    d = devices[0] if devices else None
    return EmployeeOut(
        id=emp.id,
        code=emp.code,
        full_name=emp.full_name,
        email=emp.email,
        role=emp.role,
        active=emp.active,
        enrolled=bool(d and d.enrolled_at),
        enrolled_hostname=(d.hostname if d and d.hostname else None),
        enrolled_at=(d.enrolled_at if d else None),
    )


@router.post("/auth/login", response_model=TokenOut)
async def login(body: LoginIn, request: Request, db: Annotated[AsyncSession, Depends(get_db)]) -> TokenOut:
    hit(f"login:{client_ip(request)}", limit=8, window_seconds=900)
    email = (body.email or "").strip().lower()
    result = await db.execute(select(Employee).where(Employee.email == email))
    emp = result.scalar_one_or_none()
    if not emp or not emp.password_hash or not verify_password(body.password, emp.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not emp.active:
        raise HTTPException(status_code=403, detail="Account inactive")
    # Admin/manager = full web. Employee = limited web (no finance). Agent = separate device token.
    token = create_access_token(emp)
    return TokenOut(
        access_token=token,
        role=emp.role,
        full_name=emp.full_name,
        employee_id=emp.id,
    )


@router.get("/employees", response_model=list[EmployeeOut])
async def list_employees(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Employee, Depends(require_office_or_demo)],
) -> list[EmployeeOut]:
    from app.auth import is_finance
    from app.services.data_scope import wants_demo_rows
    from sqlalchemy import or_

    demo = wants_demo_rows(user)
    if demo:
        # Demo assignee picker: sample staff only (not the demo login itself)
        q = select(Employee).where(
            Employee.active == True,  # noqa: E712
            Employee.is_demo == True,
            Employee.role == Role.employee,
        )
    else:
        # Real roster + optional demo tour login (admin/manager can manage it)
        q = select(Employee).where(
            Employee.active == True,  # noqa: E712
            or_(Employee.is_demo == False, Employee.role == Role.demo),
        )
    result = await db.execute(q.order_by(Employee.code))
    emps = list(result.scalars().all())
    if not is_finance(user):
        emps = [e for e in emps if e.role != Role.demo]
    return [await employee_to_out(db, emp) for emp in emps]


@router.post("/employees", response_model=EmployeeOut)
async def create_employee(
    body: EmployeeCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    actor: Annotated[Employee, Depends(require_manager)],
) -> EmployeeOut:
    existing = await db.execute(select(Employee).where(Employee.code == body.code))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Code already exists")
    email = (body.email or "").strip().lower() or None
    if email:
        taken = await db.execute(select(Employee).where(Employee.email == email))
        if taken.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already in use")
    if body.role == Role.admin:
        raise HTTPException(status_code=403, detail="Cannot create admin accounts from Employees")
    from app.auth import is_finance

    if body.role in (Role.manager, Role.hr, Role.demo) and not is_finance(actor):
        raise HTTPException(status_code=403, detail="Only admin/manager can create HR, manager, or demo logins")
    if body.role in (Role.employee, Role.hr, Role.demo) and (not email or not body.password):
        raise HTTPException(status_code=400, detail="Email and password required for web login")
    if body.password and len(body.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    emp = Employee(
        code=body.code,
        full_name=body.full_name,
        email=email,
        password_hash=hash_password(body.password) if body.password else None,
        role=body.role,
        is_demo=body.role == Role.demo,
    )
    db.add(emp)
    await db.commit()
    await db.refresh(emp)
    if body.role == Role.demo:
        from app.demo_seed import ensure_demo_catalog

        await ensure_demo_catalog(db)
        await db.commit()
    return await employee_to_out(db, emp)


@router.patch("/employees/{employee_id}", response_model=EmployeeOut)
async def update_employee(
    employee_id: str,
    body: EmployeeUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Employee, Depends(require_manager)],
) -> EmployeeOut:
    emp = await db.get(Employee, employee_id)
    if not emp or not emp.active:
        raise HTTPException(status_code=404, detail="Employee not found")
    if emp.role in (Role.admin, Role.manager, Role.hr):
        raise HTTPException(status_code=400, detail="Cannot edit admin/manager/HR from Employees")
    code = (body.code or "").strip()
    name = " ".join((body.full_name or "").split())
    if not code:
        raise HTTPException(status_code=400, detail="Code is required")
    if len(name) < 2:
        raise HTTPException(status_code=400, detail="Enter a full name (at least 2 characters)")
    email = (body.email or "").strip().lower() or None
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Valid login email required")
    password = (body.password or "").strip() or None
    if password is not None and len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    taken_code = await db.execute(select(Employee).where(Employee.code == code, Employee.id != emp.id))
    if taken_code.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Code already exists")
    taken_email = await db.execute(select(Employee).where(Employee.email == email, Employee.id != emp.id))
    if taken_email.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already in use")
    emp.code = code
    emp.full_name = name
    emp.email = email
    if password:
        emp.password_hash = hash_password(password)
    await db.commit()
    await db.refresh(emp)
    return await employee_to_out(db, emp)


@router.delete("/employees/{employee_id}")
async def deactivate_employee(
    employee_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    actor: Annotated[Employee, Depends(require_manager)],
) -> dict:
    """Soft-delete staff: deactivate so attendance history stays intact."""
    emp = await db.get(Employee, employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    if emp.id == actor.id:
        raise HTTPException(status_code=400, detail="You cannot remove your own account")
    from app.auth import is_finance

    if emp.role in (Role.admin, Role.manager):
        raise HTTPException(status_code=400, detail="Cannot remove admin/manager from Employees")
    if emp.role == Role.hr and not is_finance(actor):
        raise HTTPException(status_code=403, detail="Only admin/manager can remove HR accounts")
    if emp.role == Role.demo and not is_finance(actor):
        raise HTTPException(status_code=403, detail="Only admin/manager can remove demo accounts")
    emp.active = False
    emp.password_hash = None
    # Invalidate device enrollments
    devices = list((await db.execute(select(Device).where(Device.employee_id == emp.id))).scalars().all())
    for d in devices:
        d.token_hash = "revoked"
        d.enrolled_at = None
    await db.commit()
    return {"ok": True, "id": employee_id}


@router.patch("/employees/{employee_id}/credentials", response_model=EmployeeOut)
async def set_employee_credentials(
    employee_id: str,
    body: EmployeeCredentialsIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    actor: Annotated[Employee, Depends(require_manager)],
) -> EmployeeOut:
    """Admin sets/resets staff web email + password (tell them privately)."""
    emp = await db.get(Employee, employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    from app.auth import is_finance

    if emp.role in (Role.admin, Role.manager):
        raise HTTPException(status_code=400, detail="Cannot reset admin/manager credentials here")
    if emp.role == Role.hr and not is_finance(actor):
        raise HTTPException(status_code=403, detail="Only admin/manager can reset HR credentials")
    email = (body.email or "").strip().lower()
    password = (body.password or "").strip()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Valid email required")
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    taken = await db.execute(select(Employee).where(Employee.email == email, Employee.id != emp.id))
    if taken.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already in use")
    emp.email = email
    emp.password_hash = hash_password(password)
    await db.commit()
    await db.refresh(emp)
    return await employee_to_out(db, emp)


@router.post("/me/change-password")
async def change_my_password(
    body: ChangePasswordIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Employee, Depends(get_current_user)],
) -> dict:
    if not user.password_hash or not verify_password(body.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is wrong")
    if len(body.new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters")
    user.password_hash = hash_password(body.new_password)
    await db.commit()
    return {"ok": True}


@router.post("/me/change-email")
async def change_my_email(
    body: ChangeEmailIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Employee, Depends(require_manager)],
) -> dict:
    if not user.password_hash or not verify_password(body.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is wrong")
    email = (body.email or "").strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Valid email required")
    taken = await db.execute(select(Employee).where(Employee.email == email, Employee.id != user.id))
    if taken.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already in use")
    user.email = email
    await db.commit()
    return {"ok": True, "email": email}


@router.post("/me/change-display-name")
async def change_my_display_name(
    body: ChangeDisplayNameIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Employee, Depends(require_manager)],
) -> dict:
    """Admin/manager sets the name shown in the header after login."""
    name = " ".join((body.full_name or "").split())
    if len(name) < 2:
        raise HTTPException(status_code=400, detail="Enter a display name (at least 2 characters)")
    if len(name) > 120:
        raise HTTPException(status_code=400, detail="Display name is too long")
    user.full_name = name
    await db.commit()
    return {"ok": True, "full_name": name}


@router.post("/employees/{employee_id}/enroll", response_model=EnrollStartOut)
async def start_enroll(
    employee_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Employee, Depends(require_manager)],
) -> EnrollStartOut:
    emp = await db.get(Employee, employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    # Reuse a single pending enroll row instead of creating orphan devices
    pending = (
        await db.execute(
            select(Device).where(
                Device.employee_id == emp.id,
                Device.enrolled_at.is_(None),
                Device.enroll_code.is_not(None),
            )
        )
    ).scalar_one_or_none()
    code = secrets.token_hex(3).upper()
    if pending:
        pending.enroll_code = code
        device = pending
    else:
        device = Device(
            employee_id=emp.id,
            enroll_code=code,
            token_hash=hash_token(secrets.token_urlsafe(8)),  # placeholder until enroll
        )
        db.add(device)
    await db.commit()
    await db.refresh(device)
    return EnrollStartOut(device_id=device.id, enroll_code=code, employee_id=emp.id)


@router.post("/devices/enroll", response_model=EnrollCompleteOut)
async def complete_enroll(
    body: EnrollCompleteIn,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> EnrollCompleteOut:
    hit(f"enroll:{client_ip(request)}", limit=12, window_seconds=900)
    code = (body.enroll_code or "").strip().upper()
    if not code:
        raise HTTPException(status_code=400, detail="Enter the enroll code from the manager.")
    result = await db.execute(select(Device).where(Device.enroll_code == code))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(
            status_code=400,
            detail="Invalid or already used enroll code. Ask the manager for a new code.",
        )
    emp = await db.get(Employee, device.employee_id)
    if not emp:
        raise HTTPException(status_code=400, detail="Employee record missing. Contact the manager.")
    # One active PC per employee: revoke previously enrolled devices
    prior = (
        await db.execute(
            select(Device).where(
                Device.employee_id == emp.id,
                Device.id != device.id,
                Device.enrolled_at.is_not(None),
            )
        )
    ).scalars().all()
    for old in prior:
        old.token_hash = "revoked"
        old.enrolled_at = None
        old.live_status = "offline"
        old.enroll_code = None
    token = create_device_token(device.id)
    device.token_hash = hash_token(token)
    device.hostname = (body.hostname or "").strip()[:120]
    device.enrolled_at = datetime.utcnow()
    device.enroll_code = None
    device.live_status = "offline"
    await db.commit()
    return EnrollCompleteOut(
        device_id=device.id,
        device_token=token,
        employee_id=emp.id,
        employee_code=emp.code,
        employee_name=emp.full_name,
    )
