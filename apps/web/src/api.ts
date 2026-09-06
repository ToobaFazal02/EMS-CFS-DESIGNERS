const API = "";

export type LiveEmployee = {
  employee_id: string;
  code: string;
  full_name: string;
  status: string;
  last_window: string;
  last_seen_at: string | null;
  last_clicks_delta: number;
  last_keys_delta: number;
  idle_seconds: number;
  last_screenshot_url: string | null;
};

export type Employee = {
  id: string;
  code: string;
  full_name: string;
  email?: string | null;
  role: string;
  active: boolean;
  enrolled?: boolean;
  enrolled_hostname?: string | null;
  enrolled_at?: string | null;
};

function authHeaders(): HeadersInit {
  const token = localStorage.getItem("ems_token") || "";
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function apiError(r: Response, fallback: string): Promise<string> {
  try {
    const j = await r.json();
    const d = j?.detail;
    if (typeof d === "string") return d;
    if (Array.isArray(d)) return d.map((x) => x.msg || JSON.stringify(x)).join("; ");
    return fallback;
  } catch {
    return fallback;
  }
}

export class LoginError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "LoginError";
    this.status = status;
  }
}

function loginMessage(status: number, detail: string): string {
  if (status === 401) return "Email or password is incorrect.";
  if (status === 403) return "This account is inactive. Ask an administrator.";
  if (status === 422) return "Enter a valid email and password.";
  if (status === 429) return "Too many attempts. Wait a minute and try again.";
  if (status >= 500) return "Server error. Try again in a moment.";
  const clean = detail.trim();
  if (clean && !/port 8000|start the api/i.test(clean)) return clean;
  return "Could not sign in. Check your connection and try again.";
}

export async function login(email: string, password: string) {
  const payload = { email: email.trim().toLowerCase(), password };
  let r: Response;
  try {
    r = await fetch(`${API}/api/v1/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch {
    throw new LoginError("Cannot reach the server. Check your connection and try again.", 0);
  }
  if (!r.ok) {
    throw new LoginError(loginMessage(r.status, await apiError(r, "")), r.status);
  }
  try {
    return await r.json();
  } catch {
    throw new LoginError("The server sent an empty reply. Try again.", r.status || 502);
  }
}

export async function fetchLive(): Promise<LiveEmployee[]> {
  const r = await fetch(`${API}/api/v1/live`, { headers: authHeaders() });
  if (!r.ok) throw new Error("Failed to load live board");
  return r.json();
}

export type DashHourDay = { date: string; label: string; hours: number };
export type DashRosterRow = {
  employee_id: string;
  code: string;
  full_name: string;
  status: string;
  last_window: string;
  hours_today: number;
};
export type DashLateInvoice = {
  id: string;
  client_name: string;
  number: string;
  amount: number;
  currency: string;
  delayed_days: number;
};
export type DashPipeline = {
  working: number;
  waiting: number;
  on_hold: number;
  done: number;
  total: number;
  open: number;
};
export type DashFinance = {
  unpaid_count: number;
  unpaid_amount: number;
  paid_month_amount: number;
  currency: string;
  late: DashLateInvoice[];
};
export type DashboardSummary = {
  generated_at: string;
  timezone: string;
  staff_count: number;
  live_now: number;
  break_idle: number;
  offline: number;
  pipeline: DashPipeline;
  hours_this_week: DashHourDay[];
  hours_last_week: DashHourDay[];
  week_delta_hours: number;
  sparkline: number[];
  roster: DashRosterRow[];
  finance: DashFinance | null;
};

export async function fetchDashboard(signal?: AbortSignal): Promise<DashboardSummary> {
  const r = await fetch(`${API}/api/v1/dashboard`, { headers: authHeaders(), signal });
  if (r.status === 401) {
    localStorage.removeItem("ems_token");
    throw new Error("Session expired — sign in again");
  }
  if (!r.ok) throw new Error(await apiError(r, "Failed to load dashboard"));
  return r.json();
}

export async function fetchEmployees(): Promise<Employee[]> {
  const r = await fetch(`${API}/api/v1/employees`, { headers: authHeaders() });
  if (!r.ok) throw new Error("Failed to load employees");
  return r.json();
}

export async function createEmployee(body: {
  code: string;
  full_name: string;
  email?: string;
  password?: string;
  role?: string;
}) {
  const r = await fetch(`${API}/api/v1/employees`, {
    method: "POST",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(await apiError(r, "Create failed"));
  return r.json();
}

export async function updateEmployee(
  employeeId: string,
  body: {
    code: string;
    full_name: string;
    email: string;
    password?: string;
  }
) {
  const r = await fetch(`${API}/api/v1/employees/${employeeId}`, {
    method: "PATCH",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(await apiError(r, "Could not update employee"));
  return r.json() as Promise<Employee>;
}

export async function setEmployeeCredentials(employeeId: string, email: string, password: string) {
  const r = await fetch(`${API}/api/v1/employees/${employeeId}/credentials`, {
    method: "PATCH",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!r.ok) throw new Error(await apiError(r, "Could not set login"));
  return r.json() as Promise<Employee>;
}

export async function changeMyPassword(current_password: string, new_password: string) {
  const r = await fetch(`${API}/api/v1/me/change-password`, {
    method: "POST",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ current_password, new_password }),
  });
  if (!r.ok) throw new Error(await apiError(r, "Password change failed"));
  return r.json();
}

export async function changeMyEmail(email: string, current_password: string) {
  const r = await fetch(`${API}/api/v1/me/change-email`, {
    method: "POST",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ email, current_password }),
  });
  if (!r.ok) throw new Error(await apiError(r, "Email change failed"));
  return r.json() as Promise<{ ok: boolean; email: string }>;
}

export async function changeMyDisplayName(full_name: string) {
  const r = await fetch(`${API}/api/v1/me/change-display-name`, {
    method: "POST",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ full_name }),
  });
  if (!r.ok) throw new Error(await apiError(r, "Could not update display name"));
  return r.json() as Promise<{ ok: boolean; full_name: string }>;
}

export async function startEnroll(employeeId: string) {
  const r = await fetch(`${API}/api/v1/employees/${employeeId}/enroll`, {
    method: "POST",
    headers: authHeaders(),
  });
  if (!r.ok) throw new Error("Enroll failed");
  return r.json() as Promise<{ enroll_code: string; device_id: string }>;
}

export async function fetchDay(employeeId: string, date: string) {
  const r = await fetch(`${API}/api/v1/employees/${employeeId}/day?date=${date}`, {
    headers: authHeaders(),
  });
  if (!r.ok) throw new Error("Day load failed");
  return r.json();
}

export async function fetchShots(employeeId: string, date: string) {
  const r = await fetch(
    `${API}/api/v1/employees/${employeeId}/screenshots?date=${date}`,
    { headers: authHeaders() }
  );
  if (!r.ok) throw new Error("Screenshots failed");
  return r.json() as Promise<{ id: string; captured_at: string; url: string }[]>;
}

export function mediaUrl(path: string | null | undefined) {
  if (!path) return "";
  return path.startsWith("http") ? path : path;
}

export type ClientRow = {
  id: string;
  name: string;
  location: string;
  phone?: string;
  notes?: string;
};

export type InvoiceLineItem = {
  description: string;
  scope?: string;
  qty: number;
  unit_price: number;
  area?: string;
  rate?: string;
  comments?: string;
  unpaid?: boolean;
};

export type InvoiceSettings = {
  issuer_name: string;
  issuer_address: string;
  issuer_phone: string;
  issuer_email: string;
  bank_title: string;
  bank_intro: string;
  bank_account_name: string;
  bank_account_number: string;
  bank_account_type: string;
  bank_routing: string;
  bank_swift: string;
  bank_name_address: string;
  contact_name: string;
  contact_email: string;
  footer_thanks: string;
  header_color: string;
  highlight_color: string;
  updated_at?: string | null;
};

export type ProjectRow = {
  id: string;
  name: string;
  client_id: string | null;
  client_name: string;
  client_location: string;
  work_scope: string;
  assignee_id: string | null;
  assignee_name: string;
  area_sqft: number | null;
  storeys: number | null;
  phase: string;
  work_state: string;
  comments: string;
  due_at: string | null;
  target_at: string | null;
  contract_value?: number;
  deposit_pct?: number;
  currency?: string;
  paid_amount?: number;
  gate?: string;
};

export type InvoiceRow = {
  id: string;
  client_id: string;
  client_name: string;
  location: string;
  project_id: string | null;
  project_name: string;
  number: string;
  amount: number;
  currency: string;
  invoice_date: string | null;
  follow_up_at: string | null;
  status: string;
  client_comments: string;
  kind: string;
  bill_to_name: string;
  bill_to_location: string;
  bill_to_phone: string;
  line_items: InvoiceLineItem[];
  invoice_notes: string;
  delayed_days: number;
};

export async function fetchInvoices(): Promise<InvoiceRow[]> {
  const r = await fetch(`${API}/api/v1/invoices`, { headers: authHeaders() });
  if (r.status === 401) {
    localStorage.removeItem("ems_token");
    throw new Error("Session expired — sign in again");
  }
  if (!r.ok) throw new Error(await apiError(r, "Failed to load invoices"));
  return r.json();
}

export async function saveInvoice(body: Record<string, unknown>, id?: string) {
  const r = await fetch(id ? `${API}/api/v1/invoices/${id}` : `${API}/api/v1/invoices`, {
    method: id ? "PATCH" : "POST",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error((await r.json()).detail || "Save invoice failed");
  return r.json() as Promise<InvoiceRow>;
}

export async function fetchClients(): Promise<ClientRow[]> {
  const r = await fetch(`${API}/api/v1/clients`, { headers: authHeaders() });
  if (!r.ok) throw new Error("Failed to load clients");
  return r.json();
}

export async function createClient(body: { name: string; location?: string }) {
  const r = await fetch(`${API}/api/v1/clients`, {
    method: "POST",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error((await r.json()).detail || "Create client failed");
  return r.json() as Promise<ClientRow>;
}

export async function fetchProjects(): Promise<ProjectRow[]> {
  const r = await fetch(`${API}/api/v1/projects`, { headers: authHeaders() });
  if (r.status === 401) {
    localStorage.removeItem("ems_token");
    throw new Error("Session expired — sign in again");
  }
  if (!r.ok) throw new Error(await apiError(r, "Failed to load projects"));
  return r.json();
}

export async function saveProject(body: Record<string, unknown>, id?: string) {
  const r = await fetch(id ? `${API}/api/v1/projects/${id}` : `${API}/api/v1/projects`, {
    method: id ? "PATCH" : "POST",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(await apiError(r, "Save project failed"));
  return r.json() as Promise<ProjectRow>;
}

export async function deleteProject(id: string) {
  const r = await fetch(`${API}/api/v1/projects/${id}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  if (r.status === 401) {
    localStorage.removeItem("ems_token");
    throw new Error("Session expired — sign in again");
  }
  if (!r.ok) throw new Error(await apiError(r, "Delete project failed"));
  return r.json() as Promise<{ ok: boolean; id: string }>;
}

export async function deleteInvoice(id: string) {
  const r = await fetch(`${API}/api/v1/invoices/${id}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  if (r.status === 401) {
    localStorage.removeItem("ems_token");
    throw new Error("Session expired — sign in again");
  }
  if (!r.ok) throw new Error(await apiError(r, "Delete invoice failed"));
  return r.json() as Promise<{ ok: boolean; id: string }>;
}

export async function fetchInvoiceSettings(): Promise<InvoiceSettings> {
  const r = await fetch(`${API}/api/v1/invoice-settings`, { headers: authHeaders() });
  if (r.status === 401) {
    localStorage.removeItem("ems_token");
    throw new Error("Session expired — sign in again");
  }
  if (!r.ok) throw new Error(await apiError(r, "Failed to load invoice template"));
  return r.json();
}

export async function saveInvoiceSettings(body: InvoiceSettings): Promise<InvoiceSettings> {
  const r = await fetch(`${API}/api/v1/invoice-settings`, {
    method: "PATCH",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(await apiError(r, "Save invoice template failed"));
  return r.json();
}

export async function deleteEmployee(id: string) {
  const r = await fetch(`${API}/api/v1/employees/${id}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  if (r.status === 401) {
    localStorage.removeItem("ems_token");
    throw new Error("Session expired — sign in again");
  }
  if (!r.ok) throw new Error(await apiError(r, "Remove employee failed"));
  return r.json() as Promise<{ ok: boolean; id: string }>;
}

export const EXPENSE_CATEGORIES = [
  { id: "tea_water", label: "Tea / water" },
  { id: "electricity", label: "Electricity" },
  { id: "gas", label: "Gas" },
  { id: "solar", label: "Solar" },
  { id: "bills", label: "Bills" },
  { id: "parties", label: "Parties / events" },
  { id: "other", label: "Other" },
] as const;

export type ExpenseItem = {
  id: string;
  spent_on: string;
  category: string;
  amount_pkr: number;
  vendor_note: string;
  receipt_name: string;
  receipt_url?: string | null;
  created_by_id?: string | null;
  created_at?: string | null;
};

export type ExpenseMonthBucket = {
  month: number;
  total_pkr: number;
  count: number;
};

export type ExpenseMonth = {
  year: number;
  month: number;
  total_pkr: number;
  count: number;
  year_total_pkr?: number;
  year_count?: number;
  months?: ExpenseMonthBucket[];
  by_category: Record<string, number>;
  items: ExpenseItem[];
};

export async function fetchExpenses(year: number, month: number, category?: string): Promise<ExpenseMonth> {
  const q = new URLSearchParams({ year: String(year), month: String(month) });
  if (category) q.set("category", category);
  const r = await fetch(`${API}/api/v1/expenses?${q}`, { headers: authHeaders() });
  if (r.status === 401) {
    localStorage.removeItem("ems_token");
    throw new Error("Session expired — sign in again");
  }
  if (r.status === 403) throw new Error("Office access required for expenses");
  if (!r.ok) throw new Error(await apiError(r, "Failed to load expenses"));
  return r.json();
}

export async function createExpense(body: {
  spent_on: string;
  category: string;
  amount_pkr: number;
  vendor_note?: string;
  receipt?: File | null;
}): Promise<ExpenseItem> {
  const fd = new FormData();
  fd.append("spent_on", body.spent_on);
  fd.append("category", body.category);
  fd.append("amount_pkr", String(body.amount_pkr));
  fd.append("vendor_note", body.vendor_note || "");
  if (body.receipt) fd.append("receipt", body.receipt);
  const r = await fetch(`${API}/api/v1/expenses`, {
    method: "POST",
    headers: authHeaders(),
    body: fd,
  });
  if (!r.ok) throw new Error(await apiError(r, "Could not save expense"));
  return r.json();
}

export async function deleteExpense(id: string): Promise<void> {
  const r = await fetch(`${API}/api/v1/expenses/${id}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  if (!r.ok) throw new Error(await apiError(r, "Could not delete expense"));
}

export async function fetchExpenseReceipt(url: string): Promise<Blob> {
  const r = await fetch(`${API}${url}`, { headers: authHeaders() });
  if (!r.ok) throw new Error(await apiError(r, "Could not open receipt"));
  return r.blob();
}

export { authHeaders, API };
