export function invoiceStatusTextClass(status: string): string {
  const s = (status || "").toLowerCase();
  if (s === "paid") return "text-paid";
  if (s === "overdue" || s === "pending" || s === "unpaid_info") return "text-pending";
  if (s === "proforma" || s === "sent" || s === "info_sent") return "text-sent";
  return "";
}

export function invoiceStatusLabel(status: string): string {
  const s = (status || "").toLowerCase();
  if (s === "sent") return "SENT TO CLIENT";
  return (status || "").replace(/_/g, " ").toUpperCase();
}

/** Sheet column "INVOICE" — document readiness pills */
export const INVOICE_PREP = ["prepared", "preparing", "unprepared"] as const;

export function invoicePrepLabel(prep: string): string {
  return (prep || "unprepared").replace(/_/g, " ").toUpperCase();
}

export function invoicePrepTextClass(prep: string): string {
  const s = (prep || "").toLowerCase();
  if (s === "prepared") return "text-paid";
  if (s === "preparing") return "text-pending";
  return "text-sent";
}
