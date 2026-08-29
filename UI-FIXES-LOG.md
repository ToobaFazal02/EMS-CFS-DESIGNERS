# UI Fixes Applied - August 28, 2026

## Issues Fixed:

### 1. Toolbar Layout (Empty Space Between Buttons)
**Problem:** Large empty space between "Template settings" and "Refresh" buttons when not on Invoices tab.

**Fix:**
- Added `justify-content: flex-start` to `.payments-toolbar`
- Added `margin-left: auto` to last button to push Refresh button to the right side
- File: `apps/web/src/styles.css`

```css
.payments-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: flex-start;
}
.payments-toolbar > button:last-child {
  margin-left: auto;
}
```

---

### 2. Template Settings Form - Textboxes Not Full Width
**Problem:** Fields like "Section title", "Transfer instructions", "Bank name & address" were narrow (not full width).

**Fix:**
- Added CSS to make standalone fields (not inside grid) full width
- File: `apps/web/src/styles.css`

```css
.invoice-settings-form .field:not(.invoice-form-grid .field) {
  width: 100%;
  max-width: 100%;
}
.invoice-settings-form .field:not(.invoice-form-grid .field) input,
.invoice-settings-form .field:not(.invoice-form-grid .field) textarea {
  width: 100%;
  max-width: 100%;
}
```

This targets fields that are direct children of fieldset (not inside the 4-column grid) and makes them span full width.

---

### 3. Action Buttons - Inconsistent Sizing
**Problem:** View, PDF, Delete buttons were different sizes and not aligned properly.

**Fix:**
- Added `min-width: 70px`, `text-align: center`, `white-space: nowrap` to `.btn-row` and `.btn-row-del`
- File: `apps/web/src/styles.css`

```css
.btn-row {
  min-height: 34px;
  min-width: 70px;
  padding: 6px 10px;
  font-size: 13px;
  text-align: center;
  white-space: nowrap;
}

.btn-row-del {
  min-height: 36px;
  min-width: 70px;
  font-size: 13px;
  font-weight: 700;
  padding: 8px 14px;
  text-align: center;
  white-space: nowrap;
}
```

This ensures all action buttons have the same minimum width and are center-aligned.

---

## Files Modified:
1. `D:\imp\ems-cfs-designers\apps\web\src\styles.css` - All CSS fixes
2. Web app rebuilt successfully

---

## Testing:
- ✅ Web server: http://127.0.0.1:5173 (running)
- ✅ API server: http://127.0.0.1:8000 (running)
- ✅ Build completed: `dist/assets/index-nlNti8Ye.css` (36.43 kB)

---

## Next: PDF Loading Issue
User reported PDFs not loading. Need to:
1. Check API logs for PDF generation errors
2. Verify invoice settings are present in database
3. Test PDF endpoint directly
