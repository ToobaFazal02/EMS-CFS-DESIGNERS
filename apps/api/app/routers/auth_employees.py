import secrets
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import (
    create_access_token,
    create_device_token,
    get_current_user,
    hash_password,
    hash_token,
    require_manager,
    verify_password,
)
from app.db import get_db
from app.models import Device, Employee, Role
from app.schemas import (
    ChangeEmailIn,
    ChangePasswordIn,
    EmployeeCreate,
    EmployeeCredentialsIn,
    EmployeeOut,
    EnrollCompleteIn,
    EnrollCompleteOut,
    EnrollStartOut,
    LoginIn,
    TokenOut,
)

router = APIRouter(prefix="/api/v1", tags=["auth"])


@router.post("/auth/login", response_model=TokenOut)
async def login(body: LoginIn, db: Annotated[AsyncSession, Depends(get_db)]) -> TokenOut:
    result = await db.execute(select(Employee).where(Employee.email == body.email))
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
    _: Annotated[Employee, Depends(require_manager)],
) -> list[EmployeeOut]:
    result = await db.execute(select(Employee).where(Employee.active == True).order_by(Employee.code))  # noqa: E712
    emps = list(result.scalars().all())
    out: list[EmployeeOut] = []
    for emp in emps:
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
        out.append(
            EmployeeOut(
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
        )
    return out


@router.post("/employees", response_model=EmployeeOut)
async def create_employee(
    body: EmployeeCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Employee, Depends(require_manager)],
) -> Employee:
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
    if body.role == Role.employee and (not email or not body.password):
        raise HTTPException(status_code=400, detail="Email and password required for staff web login")
    if body.password and len(body.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    emp = Employee(
        code=body.code,
        full_name=body.full_name,
        email=email,
        password_hash=hash_password(body.password) if body.password else None,
        role=body.role,
    )
    db.add(emp)
    await db.commit()
    await db.refresh(emp)
    return emp


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
    if emp.role in (Role.admin, Role.manager):
        raise HTTPException(status_code=400, detail="Cannot remove admin/manager from Employees")
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
    _: Annotated[Employee, Depends(require_manager)],
) -> EmployeeOut:
    """Admin sets/resets staff web email + password (tell them privately)."""
    emp = await db.get(Employee, employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
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
    return EmployeeOut(
        id=emp.id,
        code=emp.code,
        full_name=emp.full_name,
        email=emp.email,
        role=emp.role,
        active=emp.active,
        enrolled=False,
    )


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
    db: Annotated[AsyncSession, Depends(get_db)],
) -> EnrollCompleteOut:
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
