import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, BigInteger, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Role(str, enum.Enum):
    employee = "employee"
    hr = "hr"
    demo = "demo"
    manager = "manager"
    admin = "admin"


class ExpenseCategory(str, enum.Enum):
    tea_water = "tea_water"
    electricity = "electricity"
    gas = "gas"
    solar = "solar"
    bills = "bills"
    parties = "parties"
    other = "other"


class PunchType(str, enum.Enum):
    sign_in = "sign_in"
    break_in = "break_in"
    break_out = "break_out"
    sign_out = "sign_out"


class LiveStatus(str, enum.Enum):
    offline = "offline"
    working = "working"
    break_ = "break"
    idle = "idle"


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str | None] = mapped_column(String(180), unique=True, nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[Role] = mapped_column(Enum(Role, native_enum=False), default=Role.employee)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    devices: Mapped[list["Device"]] = relationship(back_populates="employee")
    punches: Mapped[list["Punch"]] = relationship(back_populates="employee")


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    employee_id: Mapped[str] = mapped_column(ForeignKey("employees.id"), index=True)
    hostname: Mapped[str] = mapped_column(String(120), default="")
    token_hash: Mapped[str] = mapped_column(String(255))
    enroll_code: Mapped[str | None] = mapped_column(String(32), nullable=True, unique=True)
    enrolled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    live_status: Mapped[str] = mapped_column(String(20), default=LiveStatus.offline.value)
    last_window: Mapped[str] = mapped_column(String(500), default="")
    last_clicks_delta: Mapped[int] = mapped_column(Integer, default=0)
    last_keys_delta: Mapped[int] = mapped_column(Integer, default=0)
    idle_seconds: Mapped[int] = mapped_column(Integer, default=0)
    last_screenshot_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    employee: Mapped[Employee] = relationship(back_populates="devices")


class Punch(Base):
    __tablename__ = "punches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    employee_id: Mapped[str] = mapped_column(ForeignKey("employees.id"), index=True)
    type: Mapped[PunchType] = mapped_column(Enum(PunchType, native_enum=False))
    server_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    client_sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    source: Mapped[str] = mapped_column(String(40), default="agent")
    session_id: Mapped[str] = mapped_column(String(36), index=True)
    overridden_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    employee: Mapped[Employee] = relationship(back_populates="punches")


class ActivityBucket(Base):
    __tablename__ = "activity_buckets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    employee_id: Mapped[str] = mapped_column(ForeignKey("employees.id"), index=True)
    bucket_start: Mapped[datetime] = mapped_column(DateTime, index=True)
    mouse_clicks: Mapped[int] = mapped_column(Integer, default=0)
    key_presses: Mapped[int] = mapped_column(Integer, default=0)
    idle_seconds: Mapped[int] = mapped_column(Integer, default=0)


class WindowSample(Base):
    __tablename__ = "window_samples"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    employee_id: Mapped[str] = mapped_column(ForeignKey("employees.id"), index=True)
    sampled_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    title: Mapped[str] = mapped_column(String(500), default="")
    clicks: Mapped[int] = mapped_column(Integer, default=0)


class Screenshot(Base):
    __tablename__ = "screenshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    employee_id: Mapped[str] = mapped_column(ForeignKey("employees.id"), index=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    path: Mapped[str] = mapped_column(String(500))
    bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    content_type: Mapped[str] = mapped_column(String(80), default="image/jpeg")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    actor_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    action: Mapped[str] = mapped_column(String(80))
    entity: Mapped[str] = mapped_column(String(80), default="")
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ProjectPhase(str, enum.Enum):
    intake = "intake"
    preliminary_design = "preliminary_design"
    preliminary_engineering = "preliminary_engineering"
    final_engineering = "final_engineering"
    stamped_drawings = "stamped_drawings"
    field_files = "field_files"
    run_files = "run_files"


class WorkState(str, enum.Enum):
    working = "working"
    waiting = "waiting"
    on_hold = "on_hold"
    done = "done"


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(180), index=True)
    location: Mapped[str] = mapped_column(String(120), default="")
    phone: Mapped[str] = mapped_column(String(40), default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    projects: Mapped[list["Project"]] = relationship(back_populates="client")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    client_id: Mapped[str | None] = mapped_column(ForeignKey("clients.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(220), index=True)
    work_scope: Mapped[str] = mapped_column(Text, default="")
    assignee_id: Mapped[str | None] = mapped_column(ForeignKey("employees.id"), nullable=True, index=True)
    area_sqft: Mapped[float | None] = mapped_column(Float, nullable=True)
    storeys: Mapped[int | None] = mapped_column(Integer, nullable=True)
    phase: Mapped[str] = mapped_column(String(40), default=ProjectPhase.intake.value, index=True)
    work_state: Mapped[str] = mapped_column(String(20), default=WorkState.working.value)
    comments: Mapped[str] = mapped_column(Text, default="")
    due_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    target_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    client: Mapped[Client | None] = relationship(back_populates="projects")
    assignee: Mapped[Employee | None] = relationship()
    contract_value: Mapped[float] = mapped_column(Float, default=0.0)
    deposit_pct: Mapped[float] = mapped_column(Float, default=50.0)
    currency: Mapped[str] = mapped_column(String(8), default="USD")
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    invoices: Mapped[list["Invoice"]] = relationship(back_populates="project")


class InvoiceStatus(str, enum.Enum):
    proforma = "proforma"
    sent = "sent"
    pending = "pending"
    paid = "paid"
    overdue = "overdue"
    info_sent = "info_sent"
    unpaid_info = "unpaid_info"


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    client_id: Mapped[str] = mapped_column(ForeignKey("clients.id"), index=True)
    project_id: Mapped[str | None] = mapped_column(ForeignKey("projects.id"), nullable=True, index=True)
    number: Mapped[str] = mapped_column(String(80), index=True)
    amount: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String(8), default="USD")
    invoice_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    follow_up_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(24), default=InvoiceStatus.pending.value, index=True)
    client_comments: Mapped[str] = mapped_column(Text, default="")
    kind: Mapped[str] = mapped_column(String(20), default="deposit")
    bill_to_name: Mapped[str] = mapped_column(String(120), default="")
    bill_to_location: Mapped[str] = mapped_column(String(200), default="")
    bill_to_phone: Mapped[str] = mapped_column(String(40), default="")
    line_items: Mapped[str] = mapped_column(Text, default="[]")
    invoice_notes: Mapped[str] = mapped_column(Text, default="")
    # Sheet column "INVOICE": prepared | preparing | unprepared
    invoice_prep: Mapped[str] = mapped_column(String(24), default="unprepared")
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    client: Mapped[Client] = relationship()
    project: Mapped[Project | None] = relationship(back_populates="invoices")


class InvoiceSettings(Base):
    """Singleton row (id=default) — company + bank details printed on invoices."""

    __tablename__ = "invoice_settings"

    id: Mapped[str] = mapped_column(String(20), primary_key=True, default="default")
    issuer_name: Mapped[str] = mapped_column(String(120), default="")
    issuer_address: Mapped[str] = mapped_column(String(300), default="")
    issuer_phone: Mapped[str] = mapped_column(String(40), default="")
    issuer_email: Mapped[str] = mapped_column(String(120), default="")
    bank_title: Mapped[str] = mapped_column(String(80), default="USD Account Details:")
    bank_intro: Mapped[str] = mapped_column(Text, default="")
    bank_account_name: Mapped[str] = mapped_column(String(120), default="")
    bank_account_number: Mapped[str] = mapped_column(String(60), default="")
    bank_account_type: Mapped[str] = mapped_column(String(80), default="")
    bank_routing: Mapped[str] = mapped_column(String(40), default="")
    bank_swift: Mapped[str] = mapped_column(String(20), default="")
    bank_name_address: Mapped[str] = mapped_column(Text, default="")
    contact_name: Mapped[str] = mapped_column(String(120), default="")
    contact_email: Mapped[str] = mapped_column(String(120), default="")
    footer_thanks: Mapped[str] = mapped_column(String(200), default="THANK YOU FOR YOUR BUSINESS!")
    header_color: Mapped[str] = mapped_column(String(20), default="#548235")
    highlight_color: Mapped[str] = mapped_column(String(20), default="#c9a227")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class OfficeExpense(Base):
    """Studio cash-out only (tea, utilities, parties). Not client invoices."""

    __tablename__ = "office_expenses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    spent_on: Mapped[datetime] = mapped_column(DateTime, index=True)  # date stored as midnight UTC-ish; use date part
    category: Mapped[str] = mapped_column(String(40), index=True, default=ExpenseCategory.other.value)
    amount_pkr: Mapped[float] = mapped_column(Float, default=0.0)
    vendor_note: Mapped[str] = mapped_column(String(300), default="")
    receipt_name: Mapped[str] = mapped_column(String(220), default="")
    receipt_path: Mapped[str] = mapped_column(String(500), default="")
    created_by_id: Mapped[str | None] = mapped_column(ForeignKey("employees.id"), nullable=True, index=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    created_by: Mapped[Employee | None] = relationship()
