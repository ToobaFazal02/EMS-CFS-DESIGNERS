# Engineering & delivery playbook (permanent)

This is the **how we work** doc. Cursor loads the short form via `.cursor/rules/07-engineering-standards.mdc` every chat.

## Roles the agent must wear

| Role | Responsibility |
|---|---|
| Senior frontend | Consistent UI, a11y, responsive, no dead buttons (`docs/15`, `19`) |
| Backend / API | Thin routers, fat services, clear errors, versioned `/api/v1` |
| DBA | Indexes, no N+1, migrations mindset, retention jobs |
| Security | AuthZ, upload caps, no secrets, disclosed monitoring |
| Tester | Happy/edge/regression before next feature |
| Technical writer | Docs updated when behavior changes |
| Mentor | Tell user exact test steps; call human review when needed |

## Agile chunking (divide and conquer)

```
Plan slice → Implement → Self-test → Document delta → User test hint → Next slice
```

**Phase 1 suggested order (already started):**

1. Auth + employees + enroll — done baseline  
2. Punches + multi-session + hours math — done baseline  
3. Activity + idle — done baseline  
4. Screenshots — done baseline  
5. Live board + WS — done baseline  
6. Daily PDF + CSV reports — done baseline  
7. **Hardening pass** (next): clean splits, comments, indexes, agent polish, regression script  
8. Pilot on 2–3 real PCs  

Never skip hardening to jump to white-label / payroll.

## File & folder rules

| Do | Don’t |
|---|---|
| `apps/api/app/services/hours.py` | 10k-line `main.py` |
| `apps/web/src/pages/LivePage.tsx` | Business rules only in JSX |
| `apps/agent/ems_agent/capture.py` | Mix UI + HTTP + hooks in one god class forever |
| One concern per module | Copy-paste punch logic in 4 places |

**Soft limits:** ~400 lines/file; split when a file mixes HTTP + SQL + PDF + WS.

## Complexity / performance checklist

Before merging a hot path:

- Activity ingest: O(1) bucket upsert, not full-day rewrite  
- Live board: O(employees), not O(punches × employees)  
- Screenshot list by day: indexed `captured_at` + `employee_id`  
- Agent timers: don’t block Qt UI thread on HTTP  

## Testing protocol (mentor script for user)

After each slice, tell the user something like:

1. Start API + web (+ agent if needed)  
2. Login as admin  
3. Do X  
4. Expect Y  
5. If fail → paste error  

When **human review required**, say so explicitly:

- Production `.env` / secret_key  
- On-prem server install on client LAN  
- Legal monitoring notice to staff  
- Quote / scope change  

## Documentation map

| Change type | Update |
|---|---|
| New endpoint / table | `docs/10-data-model.md` + runbook |
| Product behavior | `docs/03-functional-requirements.md` |
| How to run | `docs/22-phase1-runbook.md` |
| Quality bar | this file + rule `07` |

## Definition of Done (any task)

- [ ] Code modular & named clearly  
- [ ] No obvious security hole introduced  
- [ ] Happy + one failure path tested  
- [ ] Linked modules still work  
- [ ] Docs/runbook touched if user-facing  
- [ ] User told how to verify  
