from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models import PunchType, Role


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: Role
    full_name: str
    employee_id: str


class LoginIn(BaseModel):
    email: str
    password: str


class EmployeeCreate(BaseModel):
    code: str
    full_name: str
    email: Optional[str] = None
    password: Optional[str] = None
    role: Role = Role.employee


class EmployeeCredentialsIn(BaseModel):
    email: str
    password: str


class ChangePasswordIn(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


class ChangeEmailIn(BaseModel):
    email: str
    current_password: str


class EmployeeOut(BaseModel):
    id: str
    code: str
    full_name: str
    email: Optional[str] = None
    role: Role
    active: bool
    enrolled: bool = False
    enrolled_hostname: Optional[str] = None
    enrolled_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class EnrollStartOut(BaseModel):
    device_id: str
    enroll_code: str
    employee_id: str


class EnrollCompleteIn(BaseModel):
    enroll_code: str
    hostname: str = ""


class EnrollCompleteOut(BaseModel):
    device_id: str
    device_token: str
    employee_id: str
    employee_code: str
    employee_name: str


class PunchIn(BaseModel):
    id: str = Field(..., description="Client UUID for idempotent upsert")
    type: PunchType
    client_sent_at: Optional[datetime] = None
    session_id: Optional[str] = None


class PunchOut(BaseModel):
    id: str
    type: PunchType
    server_at: datetime
    session_id: str
    employee_id: str


class ActivityIn(BaseModel):
    mouse_clicks: int = 0
    key_presses: int = 0
    window_title: str = ""
    idle_seconds: int = 0
    status: str = "working"  # working | break | idle


class LiveEmployeeOut(BaseModel):
    employee_id: str
    code: str
    full_name: str
    status: str
    last_window: str
    last_seen_at: Optional[datetime]
    last_clicks_delta: int
    last_keys_delta: int
    idle_seconds: int
    last_screenshot_url: Optional[str] = None


class DaySessionOut(BaseModel):
    session_id: str
    sign_in: Optional[datetime]
    sign_out: Optional[datetime]
    break_minutes: float
    net_hours: float
    status: str = "open"


class DaySummaryOut(BaseModel):
    employee_id: str
    date: str
    sessions: list[DaySessionOut]
    net_hours: float
    break_hours: float
    total_clicks: int
    total_keys: int
    idle_minutes: float
    punches: list[PunchOut]


class ClientIn(BaseModel):
    name: str
    location: str = ""
    notes: str = ""


class ClientOut(BaseModel):
    id: str
    name: str
    location: str = ""
    notes: str = ""
    active: bool = True


class ProjectIn(BaseModel):
    name: str
    client_id: Optional[str] = None
    work_scope: str = ""
    assignee_id: Optional[str] = None
    area_sqft: Optional[float] = None
    storeys: Optional[int] = None
    phase: str = "intake"
    work_state: str = "working"
    comments: str = ""
    due_at: Optional[datetime] = None
    target_at: Optional[datetime] = None
    contract_value: float = 0
    deposit_pct: float = 50
    currency: str = "USD"
    override_gate: bool = False
    override_reason: str = ""


class ProjectOut(BaseModel):
    id: str
    name: str
    client_id: Optional[str] = None
    client_name: str = ""
    client_location: str = ""
    work_scope: str = ""
    assignee_id: Optional[str] = None
    assignee_name: str = ""
    area_sqft: Optional[float] = None
    storeys: Optional[int] = None
    phase: str
    work_state: str
    comments: str = ""
    due_at: Optional[datetime] = None
    target_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    contract_value: float = 0
    deposit_pct: float = 50
    currency: str = "USD"
    paid_amount: float = 0
    gate: str = "ok"


class InvoiceIn(BaseModel):
    client_id: str
    project_id: Optional[str] = None
    number: str
    amount: float
    currency: str = "USD"
    invoice_date: Optional[datetime] = None
    follow_up_at: Optional[datetime] = None
    status: str = "pending"
    client_comments: str = ""
    kind: str = "deposit"


class InvoiceOut(BaseModel):
    id: str
    client_id: str
    client_name: str = ""
    location: str = ""
    project_id: Optional[str] = None
    project_name: str = ""
    number: str
    amount: float
    currency: str = "USD"
    invoice_date: Optional[datetime] = None
    follow_up_at: Optional[datetime] = None
    status: str
    client_comments: str = ""
    kind: str = "deposit"
    delayed_days: int = 0
