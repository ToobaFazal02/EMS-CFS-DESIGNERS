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

    Soft signal: unpaid deposit shows need_deposit on any phase (badge / notify).
    Hard block is applied separately — only release phases (see gate_blocks_hard).
    """
    phase = new_phase or project.phase
    value = float(project.contract_value or 0)
    if value <= 0:
        return "ok"
    paid = paid_amount(project)
    deposit = value * (float(project.deposit_pct or 50) / 100.0)
    if phase in RELEASE_PHASES and paid + 0.009 < value:
        # Prefer final when past deposit but not full; else deposit if advance missing
        if paid + 0.009 < deposit:
            return "need_deposit"
        return "need_final"
    if paid + 0.009 < deposit:
        return "need_deposit"
    return "ok"


def gate_blocks_hard(code: str, phase: str) -> bool:
    """Hard-stop only when releasing stamped / field / run files without payment."""
    if code == "need_final":
        return True
    if code == "need_deposit" and phase in RELEASE_PHASES:
        return True
    return False


def gate_error(code: str, *, audience: str = "finance", hard: bool = True) -> str:
    """Finance gets Payments instructions; HR/demo get ops-only wording (no invoice $)."""
    if audience != "finance":
        if code == "need_deposit" and hard:
            return (
                "Cannot release Stamped / Field / Run Files until Admin clears the advance."
            )
        if code == "need_final":
            return (
                "This job cannot move to Stamped / Field / Run Files yet. Ask Admin or Manager to clear the balance first."
            )
        return "Phase change blocked. Ask Admin or Manager for help."
    if code == "need_deposit":
        if hard:
            return (
                "Advance not recorded. Open Payments -> Deposit invoice for this project -> "
                "Status: Paid before Stamped Drawings / Field Files / Run Files."
            )
        return (
            "Advance not recorded yet. Design work can continue — record the deposit in Payments when ready."
        )
    if code == "need_final":
        return (
            "Final payment not recorded. Open Payments -> mark the balance Paid "
            "before Stamped Drawings / Field Files / Run Files."
        )
    return "Payment gate blocked this move."


def gate_audience(is_finance_user: bool) -> str:
    return "finance" if is_finance_user else "office"