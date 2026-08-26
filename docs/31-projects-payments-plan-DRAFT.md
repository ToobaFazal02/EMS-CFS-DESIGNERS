# Phase 3–4 plan — Projects + Payments (DRAFT, awaiting Tooba approval)

**Status:** Active plan — rebrand **done**; Projects/Payments code starts after this step.  
**Advance %:** still confirm with client (recommend 50/50).  

---

## 1. What the client actually runs today (two sheets + one queue)

### A. Payments Tracking Sheet (finance)

| Column | Software |
|---|---|
| S/No. | auto id |
| CLIENT NAME | `clients.name` |
| LOCATION | `clients.location` / country |
| INVOICE | invoice number or type (proforma vs tax) — confirm |
| INVOICE VALUE | `invoices.amount` + currency (USD/PKR) — finance role only |
| INVOICE DATE | `invoices.issued_at` |
| FOLLOW UP DATE | `invoices.follow_up_at` |
| INVOICE DELAYED (DAYS) | **computed:** today − due/follow-up — never typed by staff |
| INVOICE STATUS | enum (Paid / Pending / Overdue / Proforma / Info sent…) |
| Comments From Clients | `invoices.client_comments` |

**Safe to automate:** delayed-days, overdue badges, follow-up reminders **inside the office app**.  
**Do not automate:** bank login, scraping client email, storing card numbers, WhatsApp blast to clients without consent, public payment links until PCI/legal is decided.

### B. CFS PROJECTS — Project Details (ops)

| Column | Software |
|---|---|
| S/No. | auto |
| PROJECT NAME | `projects.name` |
| WORK SCOPE | `projects.scope` (comment on sheet = extra rules — capture as notes) |
| ASSIGNEE | FK to employee |
| AREA (sq.ft) | `projects.area_sqft` |
| Storey | `projects.storeys` |
| Status | working / waiting / on hold / done (card-level, not only phase) |
| Comments | `projects.comments` |

### C. Design Queue (market UI they want)

Inspiration: dark Kanban like **Monday / ClickUp / Linear** for CFS shops.

**Board columns (client-named, 10:18 voice):**

1. Intake  
2. Preliminary Design  
3. Preliminary Engineering  
4. Final Engineering  
5. Stamped Drawings  
6. Field Files  
7. Run Files  

Each **card:** project name, client/firm, state (Working vs Waiting), PM/assignee, **NEXT** milestone + due date (orange/red when close), target date.

Voice 10:18: deadline **turns red** when approaching — same as that company’s online queue.

---

## 2. New voice notes (10:17 / 10:18)

| Time | Meaning |
|---|---|
| 10:17 | Project module must match **their Project Details sheet**: name, assignee, area, storey, status, comments — not a generic todo list. |
| 10:18 | They saw another company’s **online** design queue (not a desktop installer). Want the same **phase columns** + visual deadline urgency. |

---

## 3. How top 1% firms stop “take the files, never pay”

Software **cannot** force a foreign client to pay. CEOs combine **policy + contract + deliverable control**. We encode the policy in the app; lawyer still owns the contract.

### Market numbers (design / professional services)

| Situation | Typical advance | Structure |
|---|---|---|
| Default CFS remote detailing (most jobs) | **50%** | 50% before Intake starts, 50% before **stamped / field / run files** leave the office |
| Large / long job | **30 / 40 / 30** or **25 / 50 / 25** | Start → mid (e.g. after Prelim Eng) → before final files |
| Repeat trusted client (clean 12 months) | **30%** start | Manager override with reason logged |
| New / slow-pay / unknown | **50% min**, optionally **100%** before final files | No override without Admin |
| Tiny job (under a threshold they set) | **100%** before start | Avoid chasing $500 invoices |

**Recommend CFS default (ask client to confirm):**

1. **50% advance** recorded as Paid (or bank proof uploaded **in-app**, not email chaos) → only then card can leave **Intake**.  
2. **Remaining 50%** due **before** Stamped Drawings / Field Files / Run Files are marked Delivered.  
3. **Hard gate:** employee **cannot** set phase to a “release” column if remaining balance > 0 (Admin override + reason).  
4. **Soft gate:** due date red at **3 days**; overdue invoice red; follow-up list for finance every morning.  
5. **Waiting** vs **Working** on the card (client delay ≠ employee delay).

**What not to copy blindly:** US **construction retainage** (5–10% holdback) is owner→contractor, opposite direction. CFS is the **consultant** — they need **deposit + file hold**, not retainage on themselves.

**Professional extras (process, not extra product bloat):**

- Quote + payment terms in writing before Intake.  
- Proforma first; work starts when deposit status = Paid.  
- Final CAD/PDF **watermarked preview** optional; **unlocked files only after final payment**.  
- Credit hold: unpaid > X days → new jobs blocked for that client.  
- Never start “as a favour” without Admin override.

**You (Tooba) ask client:** “Default 50/50, with 30% only for named trusted clients — OK?”

---

## 4. Product shape (one app, three modules)

Keep **workforce (Phase 1)** as-is. Add:

```
CFS Designers
  Live | Employees | Reports          ← existing (manager)
  Projects  (Kanban + list)           ← Phase 3
  Payments  (Excel replacement)       ← Phase 4
```

**Roles (from earlier voice):**

| Role | Projects | Payments / amounts |
|---|---|---|
| Employee | Own assigned cards; cannot see invoice $ | Never |
| Manager / HR | Full board, assign, status | Optional read-only status, **no amounts** until client says yes |
| Finance | Read project name/client/status | Full money, follow-ups, delays |
| Admin | Everything + payment gates override | Everything |

Inspiration **patterns** (not SaaS lock-in): Hubstaff (time), ClickUp/Monday (board), Harvest (invoice status) — custom FastAPI + React, on-prem.

---

## 5. What we automate (safe) vs never automate

**Automate**

- Delayed days, overdue colour, follow-up due today  
- Phase cannot skip if deposit unpaid (configurable gates)  
- “Ready to start” only when advance recorded  
- Search/filter like Design Queue  
- Export Excel matching their column names  
- Audit: who moved a card, who marked Paid  

**Do not automate (safety / legal / PCI)**

- Charging cards / Stripe until they ask + merchant account  
- Reading client Gmail/WhatsApp  
- Public unauthenticated board  
- Storing passport/CNIC scans in v1  
- Auto-emailing clients from our server without SPF/DKIM + their domain  
- Letting employees upload “paid” without finance confirmation  

---

## 6. Step-by-step build (after approval)

| Step | Work | Done when |
|---|---|---|
| 0 | Rebrand **CFS Designers** (not EMS CFS) | Client screenshots |
| 1 | Clients table (name, location) | CRUD, finance+manager |
| 2 | Projects + fields from Project Details sheet | List view = sheet |
| 3 | Kanban 7 phases + Working/Waiting + red due | Matches Design Queue |
| 4 | Payments module = Payments Tracking columns | Delayed days auto |
| 5 | Payment gates on phases | No start / no final files without $ |
| 6 | Role split (employee never finance) | API 403 tests |
| 7 | Excel import (headers only mapping) | Optional, after sample **anonymized** CSV |

---

## 7. Original start-of-project rules — in code today?

| Rule (`.cursor/rules` + `docs/05`) | In code? |
|---|---|
| Manager JWT on live/reports/employees | **Yes** `require_manager` |
| Agent device token, not shared password | **Yes** `get_device_from_token` |
| Passwords hashed (bcrypt) | **Yes** (docs said argon2; bcrypt is still hashed, OK for v1) |
| ORM / parameterized queries | **Yes** SQLAlchemy |
| Screenshots JPEG/PNG/WebP + size path | **Yes** MIME check on upload |
| Key **counts** only, no keylogger | **Yes** pynput press count |
| No clipboard hook | **Yes** |
| LIVE badge, no stealth | **Yes** |
| Server time for punches | **Yes** `datetime.utcnow` on server |
| Agent outbox, not editable truth | **Yes** |
| No PHP recorder / no cfs-designers PHP couple | **Yes** |
| Screenshot **view audit log** | **Gap** — add in hardening |
| Postgres prod | **Gap** — SQLite local now (allowed for tests) |
| CSRF cookie POSTs | **N/A** — Bearer JWT, not cookie session |

Phase 1 workforce rules **are being followed**. Phase 3–4 must add **RBAC on money** so employees never hit invoice APIs.

---

## 8. Approval checklist (Tooba)

Reply **APPROVED** or change numbers:

- [ ] Default **50%** before work, **50%** before final files  
- [ ] Trusted-client exception **30%** (named list)  
- [ ] Kanban columns = 7 names above (no extra “Final Design” unless they add it)  
- [ ] Manager **cannot** see invoice $ (or can — pick one)  
- [ ] Implement order: rebrand → Projects board → Payments → gates  

Until APPROVED: no Projects/Payments schema in the app.
