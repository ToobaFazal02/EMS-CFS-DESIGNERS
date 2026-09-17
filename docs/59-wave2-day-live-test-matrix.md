# Wave 2 — Day / Live trust — test matrix

**Date:** 17 Sep 2026  
**Shipped:** Day auto-refresh (20s) + “Updated just now” + Live update toggle + Live vs Day hint  

---

## Confirm before Wave 2 (your questions)

| Question | Answer |
|---|---|
| Dual / multi-monitor capture broken? | **No.** Still `mss.monitors[0]` = full virtual desktop (all screens stitched). Code untouched in Wave 0–2 UI work. |
| Random screenshots (not fixed 3/4/5 min)? | **Yes.** Each gap is `random(90…300)` seconds. Your 5:21 → 5:26 (~5 min) is valid random. Not a fixed clock. |
| Anything else broken from Wave 0–1? | Sign In session, idle 10s, idle shots, iPhone sound, Day name/code — leave those as-is; Wave 2 only adds Day poll. |

---

## WAVE 2 — How to test

### Happy paths

1. **Auto-refresh stats + shots**
   - Agent Sign In → keep Day page open for that person.
   - Wait for a new screenshot (up to ~5 min).
   - Within ~20s of upload, gallery + clicks/hours update **without** clicking Refresh.
   - Meta line shows **Updated just now** → **Updated Xs ago**.

2. **Live update toggle**
   - Uncheck **Live update** → auto poll stops (label: Auto-refresh off).
   - New shots only appear after manual **Refresh**.
   - Re-check → polling resumes.

3. **Lightbox survives poll**
   - Open a screenshot large view.
   - Wait 20s+ for a silent refresh.
   - Lightbox stays open (does not slam shut).

4. **Tab hidden**
   - Switch to another browser tab 30s → return.
   - Immediate refresh on focus + polling continues.

5. **PDF**
   - Staff on **own** Day: **View PDF** opens modal.
   - Admin/manager: View + **Download PDF**.
   - Staff must **not** see Download (unchanged).

6. **Live board hint**
   - Open Live → muted line explains Live (status/deltas) vs Day (totals/gallery).

### Weeping paths

| Case | Expect |
|---|---|
| Future date | Blocked; no poll spam of bad date |
| Wrong employee URL (staff) | 403 / error; no other person’s data |
| API down mid-poll | Silent poll fails quietly; manual Refresh can toast |
| Rapid date change | Only latest load wins (stale responses ignored) |
| Auto-refresh off + new shot | Gallery stale until Refresh |

### Pass criteria

- [ ] Day open → new Agent shot appears within ~20–30s without Refresh  
- [ ] “Updated just now / Xs ago” moves  
- [ ] Live update off stops auto load  
- [ ] PDF View (self) + Download (manager only)  
- [ ] Dual-monitor still one wide image when 2 screens connected  

---

## Next

Wave 3 = Phase C projects (after you pass this matrix).
