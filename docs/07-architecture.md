# Architecture

```
Employee PC                         Office LAN                    Manager browser
┌─────────────────────┐            ┌──────────────┐              ┌─────────────┐
│  EMS Agent          │            │  FastAPI     │              │  React admin│
│  PySide6 + tray     │  HTTPS     │  PostgreSQL  │  HTTPS/WSS   │  live board │
│  hooks + shots      │───────────►│  file store  │◄─────────────│  day/PDF    │
│  SQLite outbox      │  offline   │  WS /ws/live │              └─────────────┘
└─────────────────────┘  then sync └──────────────┘
```

## Data flow

1. Employee Sign In → agent event UUID → outbox → `POST /api/v1/punches`.
2. While signed in: counters + window titles batched every N seconds (`POST /api/v1/activity`).
3. Screenshot every T minutes → JPEG → `POST /api/v1/screenshots`.
4. Break pauses activity+shots (default).
5. Sign Out → punch + optional “generate PDF” job.
6. Manager live: WS events `{employee_id, status, window, clicks_delta, thumb_url}`.

## Storage

- `employees`, `devices`, `punches`, `activity_buckets` (30-min rollups), `window_samples`, `screenshots` (path + meta), `audit_log`.
- Files: `data/screenshots/{employee_id}/{yyyy}/{mm}/{dd}/{uuid}.jpg`

## Trust

- Agent may lie about *client_sent_at*. Server ignores it for hours calculation except as a warning if skew > 10 minutes.
- After sync, punch is immutable except manager override.

## Failure modes

| Failure | Behavior |
|---|---|
| API down | Agent keeps working; banner “offline, will sync” |
| Disk full | Stop shots; keep punches |
| CAD fullscreen | Tray still accessible via Win+B / hotkey |
| Duplicate sync | UUID upsert |
