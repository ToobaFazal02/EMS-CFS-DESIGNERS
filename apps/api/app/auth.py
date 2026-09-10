from datetime import datetime, timedelta
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_db
from app.models import Device, Employee, Role

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)
settings = get_settings()
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def hash_token(token: str) -> str:
    return pwd_context.hash(token)


def verify_token_hash(token: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(token, hashed)
    except Exception:
        return False


def create_access_token(employee: Employee) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": employee.id,
        "role": employee.role.value,
        "exp": expire,
        "typ": "user",
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


async def get_current_user(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Employee:
    if not creds:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = jwt.decode(creds.credentials, settings.secret_key, algorithms=[ALGORITHM])
        if payload.get("typ") != "user":
            raise HTTPException(status_code=401, detail="Invalid token type")
        emp_id = payload.get("sub")
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Invalid token") from e
    emp = await db.get(Employee, emp_id)
    if not emp or not emp.active:
        raise HTTPException(status_code=401, detail="User inactive")
    return emp


def is_finance(user: Employee) -> bool:
    """Admin / manager — client invoices and payments $."""
    return user.role in (Role.admin, Role.manager)


def is_partner(user: Employee) -> bool:
    """Faisal Khan / Asad Khan profit split — admin only. Never HR, employee, demo, or manager."""
    if user.role != Role.admin:
        return False
    blob = f"{user.full_name or ''} {user.email or ''}".casefold()
    # Named partner accounts, or the shared CFS admin login the owners already use.
    if "faisal" in blob or "asad" in blob:
        return True
    email = (user.email or "").casefold().strip()
    return email in {"admin@cfsdesigners.com", "admin@example.com"}


def is_office(user: Employee) -> bool:
    """Admin / manager / HR — real workforce, projects board, office expenses."""
    return user.role in (Role.admin, Role.manager, Role.hr)


def is_demo_user(user: Employee) -> bool:
    return user.role == Role.demo


def is_manager(user: Employee) -> bool:
    """Office ops (includes HR). Prefer is_finance() when money is involved."""
    return is_office(user)


def is_office_or_demo(user: Employee) -> bool:
    return is_office(user) or is_demo_user(user)


async def require_manager(user: Annotated[Employee, Depends(get_current_user)]) -> Employee:
    """Real office access: admin, manager, or HR (not demo, not finance-only)."""
    if not is_office(user):
        raise HTTPException(status_code=403, detail="Office access required")
    return user


async def require_office_or_demo(user: Annotated[Employee, Depends(get_current_user)]) -> Employee:
    """Office ops or isolated demo tour (never mixes real client money)."""
    if not is_office_or_demo(user):
        raise HTTPException(status_code=403, detail="Office or demo access required")
    return user


async def require_finance(user: Annotated[Employee, Depends(get_current_user)]) -> Employee:
    """Payments / invoices — HR and demo must never pass this gate."""
    if not is_finance(user):
        raise HTTPException(status_code=403, detail="Finance access required")
    return user


async def require_partner(user: Annotated[Employee, Depends(get_current_user)]) -> Employee:
    """Partner share ledger — Faisal / Asad (admin) only."""
    if not is_partner(user):
        raise HTTPException(status_code=403, detail="Partner access required")
    return user


async def require_self_or_manager(
    employee_id: str,
    user: Annotated[Employee, Depends(get_current_user)],
) -> Employee:
    """Staff may only open their own day; office roles open anyone (not demo)."""
    if is_office(user) or user.id == employee_id:
        return user
    raise HTTPException(status_code=403, detail="You can only view your own attendance")


async def get_device_from_token(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Device:
    if not creds:
        raise HTTPException(status_code=401, detail="Device token required")
    try:
        payload = jwt.decode(creds.credentials, settings.secret_key, algorithms=[ALGORITHM])
        if payload.get("typ") != "device":
            raise HTTPException(status_code=401, detail="Not a device token")
        device_id = payload.get("sub")
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Invalid device token") from e
    device = await db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=401, detail="Device not found")
    if device.token_hash == "revoked" or device.enrolled_at is None:
        raise HTTPException(status_code=401, detail="Device revoked — re-enroll with a new code")
    if device.token_hash not in ("pending",) and not verify_token_hash(creds.credentials, device.token_hash):
        raise HTTPException(status_code=401, detail="Device token invalid — re-enroll")
    return device


def create_device_token(device_id: str) -> str:
    expire = datetime.utcnow() + timedelta(days=3650)
    return jwt.encode(
        {"sub": device_id, "typ": "device", "exp": expire},
        settings.secret_key,
        algorithm=ALGORITHM,
    )
