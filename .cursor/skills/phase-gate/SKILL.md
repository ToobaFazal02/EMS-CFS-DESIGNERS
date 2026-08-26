---
name: phase-gate
description: Blocks application implementation until STATUS.md is approved. Use when the user asks to code, scaffold, or start building the EMS.
---

# Phase gate

If `STATUS.md` has `EXECUTION_APPROVED` = `no`:

- Refuse to scaffold apps/agent, apps/api, apps/web beyond placeholders.
- Offer to update docs or the question list instead.
- If the user explicitly says "approved, start building", update `STATUS.md` first, then implement Phase 1 only (`docs/09-phases-estimate.md`).
