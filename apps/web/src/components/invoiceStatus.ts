export function invoiceStatusTextClass(status: string): string {
  const s = (status || "").toLowerCase();
  if (s === "paid") return "text-paid";
  if (s === "overdue" || s === "pending" || s === "unpaid_info") return "text-pending";
  if (s === "proforma" || s === "sent" || s === "info_sent") return "text-sent";
  return "";
}

export function invoiceStatusLabel(status: string): string {
  return (status || "").replace(/_/g, " ").toUpperCase();
}
