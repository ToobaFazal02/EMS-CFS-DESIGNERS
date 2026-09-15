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


class EmployeeUpdate(BaseModel):
    code: str
    full_name: str
    email: Optional[str] = None
    password: Optional[str] = None


class EmployeeCredentialsIn(BaseModel):
    email: str
    password: str


class ChangePasswordIn(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


class ChangeEmailIn(BaseModel):
    email: str
    current_password: str


class ChangeDisplayNameIn(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120)


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


class DashHourDay(BaseModel):
    date: str
    label: str
    hours: float


class DashRosterRow(BaseModel):
    employee_id: str
    code: str
    full_name: str
    status: str
    last_window: str
    hours_today: float


class DashLateInvoice(BaseModel):
    id: str
    client_name: str
    number: str
    amount: float
    currency: str
    delayed_days: int


class DashPipeline(BaseModel):
    working: int = 0
    waiting: int = 0
    on_hold: int = 0
    done: int = 0
    total: int = 0
    open: int = 0


class DashFinance(BaseModel):
    unpaid_count: int = 0
    unpaid_amount: float = 0
    paid_month_amount: float = 0
    currency: str = "USD"
    late: list[DashLateInvoice] = Field(default_factory=list)


class DashPartnerShares(BaseModel):
    """Admin/partner-only. Never returned for HR / employee / demo / manager."""

    year: int
    month: Optional[int] = None
    currency: str = "USD"
    display_currency: str = "PKR"
    usd_pkr_rate: float = 0
    rate_date: Optional[str] = None
    rate_note: str = ""
    partner_a_name: str = "Faisal Khan"
    partner_b_name: str = "Asad Khan"
    paid_invoices_usd: float = 0
    paid_invoices_pkr: float = 0
    paid_invoice_count: int = 0
    expenses_pkr: float = 0
    expenses_usd: float = 0
    expense_count: int = 0
    net_usd: float = 0
    net_pkr: float = 0
    faisal_share_usd: float = 0
    faisal_share_pkr: float = 0
    asad_share_usd: float = 0
    asad_share_pkr: float = 0
    split_percent: int = 50


class PartnerSharePaidRow(BaseModel):
    id: str
    number: str = ""
    client_name: str = ""
    amount: float = 0
    amount_usd: Optional[float] = None
    amount_pkr: Optional[float] = None
    currency: str = "USD"
    invoice_date: Optional[str] = None
    usd_pkr_rate: Optional[float] = None
    rate_date: Optional[str] = None
    in_pool: bool = True


class PartnerShareExpenseRow(BaseModel):
    id: str
    spent_on: str = ""
    category: str = ""
    amount_pkr: float = 0
    amount_usd: float = 0
    usd_pkr_rate: float = 0
    rate_date: str = ""
    vendor_note: str = ""


class PartnerSharesOut(DashPartnerShares):
    paid_rows: list[PartnerSharePaidRow] = Field(default_factory=list)
    expense_rows: list[PartnerShareExpenseRow] = Field(default_factory=list)


class DashboardOut(BaseModel):
    generated_at: str
    timezone: str = "Asia/Karachi"
    staff_count: int
    live_now: int
    break_idle: int
    offline: int
    pipeline: DashPipeline
    hours_this_week: list[DashHourDay]
    hours_last_week: list[DashHourDay]
    week_delta_hours: float
    sparkline: list[float]
    roster: list[DashRosterRow]
    finance: Optional[DashFinance] = None
    partner_shares: Optional[DashPartnerShares] = None


class ClientIn(BaseModel):
    name: str
    location: str = ""
    phone: str = ""
    notes: str = ""


class ClientOut(BaseModel):
    id: str
    name: str
    location: str = ""
    phone: str = ""
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


class InvoiceLineItemIn(BaseModel):
    description: str = Field(..., min_length=1, max_length=500)
    scope: str = Field("", max_length=200)
    qty: float = Field(default=1.0, gt=0, le=99999)
    unit_price: float = Field(default=0.0, ge=0, le=1_000_000_000)
    area: str = Field("", max_length=80)
    rate: str = Field("", max_length=80)
    comments: str = Field("", max_length=500)
    unpaid: bool = False
    cell_colors: dict[str, str] = Field(default_factory=dict)


class InvoiceSettingsIn(BaseModel):
    issuer_name: str = Field("", max_length=120)
    issuer_address: str = Field("", max_length=300)
    issuer_phone: str = Field("", max_length=40)
    issuer_email: str = Field("", max_length=120)
    bank_title: str = Field("USD Account Details:", max_length=80)
    bank_intro: str = Field("", max_length=4000)
    bank_account_name: str = Field("", max_length=120)
    bank_account_number: str = Field("", max_length=60)
    bank_account_type: str = Field("", max_length=80)
    bank_routing: str = Field("", max_length=40)
    bank_swift: str = Field("", max_length=20)
    bank_name_address: str = Field("", max_length=2000)
    contact_name: str = Field("", max_length=120)
    contact_email: str = Field("", max_length=120)
    footer_thanks: str = Field("THANK YOU FOR YOUR BUSINESS!", max_length=200)
    header_color: str = Field("#548235", max_length=20)
    highlight_color: str = Field("#c9a227", max_length=20)


class InvoiceSettingsOut(InvoiceSettingsIn):
    updated_at: Optional[datetime] = None


class InvoiceIn(BaseModel):
    client_id: str
    project_id: Optional[str] = None
    number: str
    amount: float = 0
    currency: str = "USD"
    invoice_date: Optional[datetime] = None
    follow_up_at: Optional[datetime] = None
    status: str = "pending"
    client_comments: str = Field("", max_length=4000)
    kind: str = "deposit"
    invoice_prep: str = Field("unprepared", max_length=24)
    bill_to_name: str = Field("", max_length=120)
    bill_to_location: str = Field("", max_length=200)
    bill_to_phone: str = Field("", max_length=40)
    line_items: list[InvoiceLineItemIn] = Field(default_factory=list)
    invoice_notes: str = Field("", max_length=4000)


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
    invoice_prep: str = "unprepared"
    bill_to_name: str = ""
    bill_to_location: str = ""
    bill_to_phone: str = ""
    line_items: list[InvoiceLineItemIn] = Field(default_factory=list)
    invoice_notes: str = ""
    delayed_days: int = 0


EXPENSE_CATEGORIES = (
    "tea_water",
    "electricity",
    "gas",
    "solar",
    "bills",
    "parties",
    "other",
)


class ExpenseIn(BaseModel):
    spent_on: str = Field(..., description="YYYY-MM-DD (Asia/Karachi calendar day)")
    category: str
    amount_pkr: float = Field(..., gt=0, le=50_000_000)
    vendor_note: str = Field("", max_length=300)
    receipt_name: str = Field("", max_length=220)


class ExpenseOut(BaseModel):
    id: str
    spent_on: str
    category: str
    amount_pkr: float
    vendor_note: str = ""
    receipt_name: str = ""
    receipt_url: Optional[str] = None
    created_by_id: Optional[str] = None
    created_at: Optional[datetime] = None


class ExpenseMonthBucket(BaseModel):
    month: int
    total_pkr: float
    count: int


class ExpenseMonthOut(BaseModel):
    year: int
    month: int
    total_pkr: float
    count: int
    year_total_pkr: float = 0
    year_count: int = 0
    months: list[ExpenseMonthBucket] = Field(default_factory=list)
    by_category: dict[str, float]
    items: list[ExpenseOut]
