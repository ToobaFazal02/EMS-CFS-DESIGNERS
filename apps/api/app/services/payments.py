from datetime import date, datetime
import re

from app.models import Invoice, InvoiceStatus, Project, ProjectPhase

RELEASE_PHASES = {
    ProjectPhase.stamped_drawings.value,
    ProjectPhase.field_files.value,
    ProjectPhase.run_files.value,
}

INVOICE_STATUSES = [s.value for s in InvoiceStatus]

_CURRENCY_RE = re.compile(r"^[A-Z]{3}$")


def normalize_currency(raw: str | None) -> str:
    code = (raw or "USD").strip().upper()
    if not _CURRENCY_RE.match(code):
        raise ValueError("Invalid currency code")
    return code


def delayed_days(inv: Invoice, today: date | None = None) -> int:
    if (inv.status or "") == InvoiceStatus.paid.value:
        return 0
    today = today or date.today()
    anchor = inv.follow_up_at or inv.invoice_date
    if not anchor:
        return 0
    d = anchor.date() if isinstance(anchor, datetime) else anchor
    n = (today - d).days
    return max(n, 0)


def paid_amount(project: Project) -> float:
    total = 0.0
    for inv in project.invoices or []:
        if (inv.status or "") == InvoiceStatus.paid.value:
            total += float(inv.amount or 0)
    return round(total, 2)


def gate_status(project: Project, new_phase: str | None = None) -> str:
    """ok | need_deposit | need_final.

    When new_phase is None (board display), unpaid jobs still in Intake show
    need_deposit so staff see the block before they try to move the card.
    """
    phase = new_phase or project.phase
    value = float(project.contract_value or 0)
    if value <= 0:
        return "ok"
    paid = paid_amount(project)
    deposit = value * (float(project.deposit_pct or 50) / 100.0)
    viewing = new_phase is None
    if phase == ProjectPhase.intake.value and viewing and paid + 0.009 < deposit:
        return "need_deposit"
    if phase != ProjectPhase.intake.value and paid + 0.009 < deposit:
        return "need_deposit"
    if phase in RELEASE_PHASES and paid + 0.009 < value:
        return "need_final"
    return "ok"


def gate_error(code: str, *, audience: str = "finance") -> str:
    """Finance gets Payments instructions; HR/demo get ops-only wording (no invoice $)."""
    if audience != "finance":
        if code == "need_deposit":
            return (
                "This job cannot leave Intake yet. Ask Admin or Manager to clear the advance first."
            )
        if code == "need_final":
            return (
                "This job cannot move to Stamped / Field / Run Files yet. Ask Admin or Manager to clear the balance first."
            )
        return "Phase change blocked. Ask Admin or Manager for help."
    if code == "need_deposit":
        return (
            "Advance not recorded. Go to Payments → add a Deposit invoice for this "
            "project → set status to Paid (default: 50% of contract before leaving Intake)."
        )
    if code == "need_final":
        return (
            "Final payment not recorded. In Payments, mark the balance Paid before "
            "Stamped Drawings / Field Files / Run Files."
        )
    return "Payment gate blocked this move."


def gate_audience(is_finance_user: bool) -> str:
    return "finance" if is_finance_user else "office"