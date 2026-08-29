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


async def require_manager(user: Annotated[Employee, Depends(get_current_user)]) -> Employee:
    if user.role not in (Role.manager, Role.admin):
        raise HTTPException(status_code=403, detail="Manager access required")
    return user


def is_manager(user: Employee) -> bool:
    return user.role in (Role.manager, Role.admin)


async def require_self_or_manager(
    employee_id: str,
    user: Annotated[Employee, Depends(get_current_user)],
) -> Employee:
    """Staff may only open their own day; managers/admins open anyone."""
    if is_manager(user) or user.id == employee_id:
        return user
    raise HTTPException(status_code=403, detail="You can only view your own attendance")


async def get_device_from_token(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Device:
    if not creds:
        raise HTTPException(status_code=401, detail="Device token required")
    # Device tokens are opaque; look up by verifying hash against active devices is expensive.
    # Phase 1: JWT-shaped device token with typ=device
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
    # Bind JWT to stored hash so a forged/stolen device_id JWT cannot impersonate
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
