# Design Queue + Payments — client flow & senior QA matrix

**Date:** 18 Sep 2026  
**Apps:** Web / Manager desktop · Agent  
**Slice:** Detailer + Engineer roles · MissingGreenlet fix · human errors · Payments deep-link

---

## How the client should use it (happy path)

```
1) Admin/Manager  →  Clients: add firm (name + Initial + location)
2) Anyone allowed →  Projects: New project in Intake
                      · Name, client, scope
                      · Detailer * + Engineer * (same person allowed)
                      · Contract $ + Deposit % (Admin/Manager only)
                      · Code: leave blank → auto Initial+DDMMYY (PKT)
3) Admin/Manager  →  Payments: Deposit invoice for that project → Status Paid
                      (amount = deposit % of contract, default 50%)
4) Admin/Manager  →  Projects board: move card Intake → Prelim Design → …
5) Detailer/Engineer → Work the job; log daily progress % on Edit
6) Near release   →  Payments: Balance Paid before Stamped / Field / Run Files
```

**Important:** Design phases (Intake → Final Eng.) are **not** hard-blocked on unpaid deposit. Cards show **Advance pending / Deposit due**. Hard stop only at **Stamped / Field / Run Files**. Leaving Intake unpaid writes an admin audit `deposit_unpaid_phase_advance`.

**Staff privacy (client req):** staff see **`[Initial] · location` only** — never real firm names. Admin/Manager/HR see full names. Use unique Initials (DE/DM) when two clients share a letter.

---

## Client WhatsApp lock (18 Sep)

- Multiple assign = **Detailer** + **Engineer** (two role slots), not random N checkboxes
- Every project has its own Detailer and Engineer
- Same person may fill both roles

---

## Errors (trust)

| Bad (never ship to client) | Good |
|---|---|
| `Could not save project (MissingGreenlet)` | `Could not save project. Please try again…` |
| Silent fail | Red field + plain message (Detailer required, etc.) |

---

## Roles — sign in and test

| Role | Projects | Payments |
|---|---|---|
| **Admin / Manager** | Full board + $ + D/E + override | Full + deep-link |
| **HR** | Ops board; no contract $ | Blocked |
| **Employee** | Create/edit if D or E; Intake on create; masked clients | Blocked |

---

## Feature test data

### A. Happy — Admin create + deposit + move

| Field | Value |
|---|---|
| Client | Existing with Initial |
| Project name | `LOT 12 QA Horning` |
| Code | *(blank)* |
| Scope | Detailing + Engineering |
| Detailer | Staff A |
| Engineer | Staff B (or same as A) |
| Phase | **Intake** |
| Contract | `30000` USD |
| Deposit % | `50` |

**Expect:** Save OK. Card shows `D: … · E: …`. Deposit due badge.  
Payments → deep link → Deposit `15000` → **Paid** → move to Prelim Design OK.

### B. Gate unhappy

Move without Paid deposit → toast + **Open Payments → record deposit**; Phase highlighted if save blocked.

### C. Staff create

| Field | Value |
|---|---|
| Name | `Plot 10 a` |
| Client | `[D] · usa` style |
| Detailer | self |
| Engineer | self or teammate |
| Area / Storey | sensible (`1200` / `2`) |

**Expect:** Save OK; code auto; no contract fields.

### D. Validation

| Case | Expect |
|---|---|
| Missing Detailer or Engineer | Red field + toast |
| Storey `3000` / huge area | Red reject |
| Short name `ab` | Fail |

### E. Access

Engineer-only member sees job in My Projects and can log %. Unassigned staff does not.

---

## Regression checklist

- [ ] Admin: Intake + contract + D/E save OK (no MissingGreenlet)
- [ ] Card shows D: and E:
- [ ] Move without deposit → gate + Payments deep-link
- [ ] Paid deposit → move OK
- [ ] Staff create with both roles OK
- [ ] Toast never shows exception class names
- [ ] Version footer still visible

---

## After pull

1. Restart **API** (schema_patch migrates assignee roles once)  
2. Refresh web / Vite  
3. Walk this matrix before next wave

## Client-facing flow poster

Shareable diagram: [`cfs-design-queue-flow-poster.png`](cfs-design-queue-flow-poster.png)  
(Client → Project D+E → Intake → Payments Paid → Kanban → Daily % → Final pay)
