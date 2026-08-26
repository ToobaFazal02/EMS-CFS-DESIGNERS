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

export async function login(email: string, password: string) {
  const r = await fetch(`${API}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!r.ok) throw new Error((await r.json()).detail || "Login failed");
  return r.json();
}

export async function fetchLive(): Promise<LiveEmployee[]> {
  const r = await fetch(`${API}/api/v1/live`, { headers: authHeaders() });
  if (!r.ok) throw new Error("Failed to load live board");
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
  notes?: string;
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

export { authHeaders, API };
