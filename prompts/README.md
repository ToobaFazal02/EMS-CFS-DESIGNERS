# Prompts (copy into Cursor after this folder is the workspace)

You should rarely need these if rules loaded. Use when starting a **new** chat.

## New chat — planning only

```
Read STATUS.md, AGENTS.md, and docs/00-executive-brief.md.
Do not write application code.
Summarize remaining open questions from docs/08-open-questions-client.md.
```

## New chat — after client replies

```
Update docs/08-open-questions-client.md with these answers:
<paste>
Then say what is now locked vs still blocking Phase 1.
Do not implement yet unless STATUS.md is approved.
```

## New chat — implementation (only after approval)

```
STATUS.md is approved. Implement Phase 1 only as docs/09-phases-estimate.md.
Follow .cursor/rules and docs/07-architecture.md.
Keystroke counts only. No stealth mode.
```
