# Data storage — where everything lives (professional)

## Rule

**System of record = your EMS server database + file store.**  
Google Sheet is export only. Employee PC SQLite is **temporary outbox**, not truth.

## Recommended layout (v1)

```
Office server (or one dedicated mini-PC on LAN)
├── PostgreSQL          → punches, users, activity buckets, metadata
├── data/screenshots/   → JPEG files (not inside DB blobs)
├── data/reports/       → generated PDFs
└── backups/            → nightly DB + screenshots archive
```

| Data | Where | Why |
|---|---|---|
| Sign in / break / sign out | PostgreSQL | Server time, anti-cheat, queryable |
| Click / key counts, window titles | PostgreSQL (rolled into 30‑min buckets + samples) | Reports + live |
| Screenshots | Disk folders + DB row (path, time, employee) | DB bloated na ho; files easy to purge |
| PDF reports | Disk + optional link in DB | Same as TimesheetV2 output, central |
| Agent offline queue | Local SQLite on PC | Sync when server reachable, then clear |

## On-prem vs cloud (locked recommendation)

| | On-prem (default) | Cloud VPS |
|---|---|---|
| Attendance + activity | OK | OK |
| CAD screenshots | **Preferred** (client drawings stay inside) | Only if client accepts drawings on internet |
| Manager at home | VPN to office | Direct HTTPS |

**Professionally for CFS:** start **on-prem**. Manager ghar se = WireGuard/OpenVPN office server ko. Raw screenshots public SaaS pe mat daalo unless client explicitly signs off.

## Retention (professional default)

- Screenshots: **60 days**, then auto-delete  
- Punches / hours: **1+ years** (payroll disputes)  
- Nightly backup: DB dump + screenshots zip to external disk  

## Security basics

- Manager login (hashed passwords)  
- Each PC = enrolled device token  
- HTTPS on LAN if possible; at least firewall so only office PCs hit API  
- Employees cannot edit synced punches  

## Scale

12 employees ≈ hundreds of MB screenshots/day at 5‑min interval — fine on a 50 GB VPS disk with 60‑day retention. 50 employees = same design, bigger disk / shorter retention if needed. No redesign required for “mazeed employees”.
