# Wave 3 Phase C (C1–C5) — test matrix

**Date:** 17 Sep 2026  
**Slice:** Client initial/invoice · project code · scope enum · staff create + multi-assignee · daily %  
**Not in this slice:** C6 full client-name hiding for employees (code shown; full name still visible for now)

---

## Pre-check

| Check | Expect |
|---|---|
| DB | No wipe — existing `ems.db` kept; new columns/tables via `create_all` + `schema_patch` |
| Restart API | After pull, restart so router + models load |
| Web rebuild | `npm run build` (or Vite dev) for Projects UI |

---

## C1 — Client master (initial + invoice status)

### Happy

1. **Office add client** — Admin/manager/HR: name + **Initial** (required) + location + invoice status → Add client succeeds; initial uppercased (e.g. `w` → `W`).
2. **Staff list clients** — Employee opens Projects → client dropdown populated (no phone/notes).
3. **PATCH client** (API) — `PATCH /api/v1/clients/{id}` with initial + invoice_status updates row.

### Weeping

| Case | Expect |
|---|---|
| Client without initial | 400 — “Client initial is required” |
| Invalid invoice_status | 400 |
| Employee POST /clients | 403 (office/demo only) |
| Employee sees phone/notes | Empty / hidden |

---

## C2 — Project code (`Initial` + `DDMMYY` PKT)

### Happy

1. Create project with client initial `D`, leave Code blank → code like `D170926` (PKT date).
2. Override Code with `CUSTOM-01` → saved as sanitized uppercase override.
3. Card + list show **code** prominently (gold).

### Weeping

| Case | Expect |
|---|---|
| Client missing / wrong demo scope | 400 Client not found |
| Empty name / short name | 400 (existing validation) |

---

## C3 — Scope enum

### Happy

1. Scope select only: Estimation / Detailing / Detailing + Engineering.
2. `GET /api/v1/project-phases` returns `scopes` + `scope_labels`.
3. Saved `work_scope` is enum value (`estimation`, `detailing`, `detailing_engineering`).

### Weeping

| Case | Expect |
|---|---|
| Free-text / invalid scope on **new** project | 400 |
| Kanban move on legacy free-text scope | May 400 until user sets a valid scope once in Edit |

---

## C4 — Staff create + multi-assignee

### Happy

1. **Employee** sees **New project** / + Add a card; can create with client + scope; self pre-checked as assignee.
2. Multi-check assignees → lead = first checked; `assignee_id` + `project_assignees` rows match.
3. Employee list shows only projects where they are lead **or** in assignees.
4. Manager/admin/HR see all (demo-scoped).
5. Staff/HR create: contract forced **0** (no $ fields). Finance still requires contract > 0.
6. Payment gate unchanged for finance phase moves (need_deposit / need_final / override).

### Weeping

| Case | Expect |
|---|---|
| Employee creates with **no** assignees (untick self) | Project created but **not** in their list (assignee membership filter) |
| Employee PATCH project they are **not** on | 403 |
| Invalid assignee id | 400 |
| Staff cannot delete project | Delete still finance-only |

---

## C5 — Daily progress %

### Happy

1. Edit assigned project → enter percent + note → **Save progress**.
2. Same day + same person → upsert (updates row).
3. Card/list shows `latest_progress_pct` (max for today, else latest row).
4. History list under edit form (recent rows).

### Weeping

| Case | Expect |
|---|---|
| Percent &lt; 0 or &gt; 100 | 400 |
| Progress on unassigned project (staff) | 403 |
| Staff logging for another employee_id | 403 (managers may) |

---

## Regression (do not break)

- [ ] Finance kanban move still hits payment gate when unpaid
- [ ] Override & move still finance-only
- [ ] HR still no contract fields / no Payments nudge
- [ ] Staff still hide_money (contract 0, gate ok in API out)
- [ ] Demo catalog still isolated (`is_demo`)

---

## Pass criteria (C1–C5)

- [ ] Client requires initial; invoice status selectable  
- [ ] Auto code + override works; code visible on cards  
- [ ] Scope enum only; phases endpoint has scopes  
- [ ] Employee can create + multi-assign; list = assignee membership  
- [ ] Daily % save + history; payment gates still work  

---

## Next

C6 role-aware client display polish · Wave 4 Desktop Setup rebuild after C verified.
