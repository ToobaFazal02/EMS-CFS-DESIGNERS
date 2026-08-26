# Data model (draft)

```
employees (id, code, full_name, role, active, created_at)
devices (id, employee_id, hostname, device_token_hash, enrolled_at, last_seen_at)
punches (id uuid, employee_id, type enum, server_at, client_sent_at, source, overridden_by, reason)
activity_buckets (id, employee_id, bucket_start, mouse_clicks, key_presses)
window_samples (id, employee_id, sampled_at, title, clicks)
screenshots (id uuid, employee_id, captured_at, path, bytes, content_type)
audit_log (id, actor_id, action, entity, payload_json, at)
```

Punch `type`: `sign_in` | `break_in` | `break_out` | `sign_out`.

Hours are **computed**, never stored as the only source (store punches; derive net hours in queries/reports).
