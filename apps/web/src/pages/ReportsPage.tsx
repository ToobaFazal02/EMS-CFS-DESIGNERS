import { useMemo, useState } from "react";
import { fetchAuthedBlob, triggerBlobDownload } from "../api";
import { PdfPreviewModal } from "../components/PdfPreviewModal";
import { useToast } from "../components/ToastProvider";

function todayLocalISO(): string {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Karachi",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date());
}

function isFutureDay(iso: string): boolean {
  return iso > todayLocalISO();
}

function isFutureMonth(year: number, month: number): boolean {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Karachi",
    year: "numeric",
    month: "numeric",
  }).formatToParts(new Date());
  const y = Number(parts.find((p) => p.type === "year")?.value);
  const m = Number(parts.find((p) => p.type === "month")?.value);
  return year > y || (year === y && month > m);
}

type PreviewState = {
  title: string;
  headers: string[];
  rows: string[][];
} | null;

export function ReportsPage() {
  const toast = useToast();
  const maxDate = useMemo(() => todayLocalISO(), []);
  const [date, setDate] = useState(maxDate);
  const [year, setYear] = useState(new Date().getFullYear());
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [preview, setPreview] = useState<PreviewState>(null);
  const [pdfPreview, setPdfPreview] = useState<{ url: string; title: string } | null>(null);

  async function fetchBlob(path: string): Promise<Blob | null> {
    const res = await fetchAuthedBlob(path);
    if ("error" in res) {
      toast.error(res.error);
      return null;
    }
    return res.blob;
  }

  async function download(path: string, filename: string) {
    const blob = await fetchBlob(path);
    if (!blob) return;
    triggerBlobDownload(blob, filename);
  }

  async function viewPdf(path: string, title: string) {
    const blob = await fetchBlob(path);
    if (!blob) return;
    if (pdfPreview?.url) URL.revokeObjectURL(pdfPreview.url);
    setPdfPreview({ url: URL.createObjectURL(blob), title });
  }

  function closePdfPreview() {
    if (pdfPreview?.url) URL.revokeObjectURL(pdfPreview.url);
    setPdfPreview(null);
  }

  async function viewCsv(path: string, title: string) {
    const blob = await fetchBlob(path);
    if (!blob) return;
    const text = await blob.text();
    const lines = text.replace(/^\ufeff/, "").trim().split(/\r?\n/).filter(Boolean);
    if (!lines.length) {
      setPreview({ title, headers: [], rows: [] });
      return;
    }
    const parse = (line: string) => {
      const out: string[] = [];
      let cur = "";
      let q = false;
      for (let i = 0; i < line.length; i++) {
        const ch = line[i];
        if (ch === '"') {
          q = !q;
          continue;
        }
        if (ch === "," && !q) {
          out.push(cur.replace(/^'/, ""));
          cur = "";
          continue;
        }
        cur += ch;
      }
      out.push(cur.replace(/^'/, ""));
      return out;
    };
    const headers = parse(lines[0]);
    const rows = lines.slice(1).map(parse);
    setPreview({ title, headers, rows });
  }

  function guardDayThen(fn: () => void) {
    if (!date || !/^\d{4}-\d{2}-\d{2}$/.test(date)) {
      toast.error("Pick a valid date.");
      return;
    }
    if (isFutureDay(date)) {
      toast.error(`Future dates are not allowed. Today is ${maxDate}.`);
      return;
    }
    fn();
  }

  function guardMonthThen(fn: () => void) {
    if (!Number.isInteger(year) || year < 2000 || year > 2100) {
      toast.error("Year must be between 2000 and 2100.");
      return;
    }
    if (!Number.isInteger(month) || month < 1 || month > 12) {
      toast.error("Month must be 1–12.");
      return;
    }
    if (isFutureMonth(year, month)) {
      toast.error("Future months are not allowed.");
      return;
    }
    fn();
  }

  const monthPad = String(month).padStart(2, "0");

  return (
    <div>
      <PdfPreviewModal
        open={Boolean(pdfPreview)}
        title={pdfPreview?.title}
        blobUrl={pdfPreview?.url || null}
        onClose={closePdfPreview}
      />
      <h2>Reports</h2>

      <div className="card" style={{ marginBottom: 16 }}>
        <h3>Daily attendance</h3>
        <div className="toolbar">
          <div className="field date-field">
            <label htmlFor="report-date">Date</label>
            <div className="date-wrap">
              <input
                id="report-date"
                type="date"
                max={maxDate}
                value={date}
                onChange={(e) => {
                  setDate(e.target.value);
                }}
              />
              <span className="date-icon" aria-hidden>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                  <rect x="3" y="5" width="18" height="16" rx="2" stroke="#C9A227" strokeWidth="2" />
                  <path d="M3 10h18M8 3v4M16 3v4" stroke="#C9A227" strokeWidth="2" strokeLinecap="round" />
                </svg>
              </span>
            </div>
          </div>
          <button
            type="button"
            className="secondary"
            onClick={() =>
              guardDayThen(() => viewCsv(`/api/v1/reports/attendance.csv?date=${date}`, `Daily — ${date}`))
            }
          >
            View table
          </button>
          <button
            type="button"
            onClick={() =>
              guardDayThen(() =>
                download(`/api/v1/reports/attendance.xlsx?date=${date}`, `EMS_Attendance_${date}.xlsx`)
              )
            }
          >
            Download Excel
          </button>
          <button
            type="button"
            className="secondary"
            onClick={() =>
              guardDayThen(() =>
                download(`/api/v1/reports/attendance.csv?date=${date}`, `attendance_${date}.csv`)
              )
            }
          >
            Download CSV
          </button>
        </div>
      </div>

      <div className="card" style={{ marginBottom: 16 }}>
        <h3>Monthly compile</h3>
        <div className="toolbar">
          <div className="field">
            <label>Year</label>
            <input
              type="number"
              min={2000}
              max={new Date().getFullYear()}
              value={year}
              onChange={(e) => {
                setYear(Number(e.target.value));
              }}
            />
          </div>
          <div className="field">
            <label>Month</label>
            <input
              type="number"
              min={1}
              max={12}
              value={month}
              onChange={(e) => {
                setMonth(Number(e.target.value));
              }}
            />
          </div>
          <button
            type="button"
            className="secondary"
            onClick={() =>
              guardMonthThen(() =>
                viewCsv(
                  `/api/v1/reports/monthly.csv?year=${year}&month=${month}`,
                  `Monthly — ${year}-${monthPad}`
                )
              )
            }
          >
            View table
          </button>
          <button
            type="button"
            className="secondary"
            onClick={() =>
              guardMonthThen(() =>
                viewPdf(
                  `/api/v1/reports/monthly.pdf?year=${year}&month=${month}&inline=1`,
                  `Monthly PDF — ${year}-${monthPad}`
                )
              )
            }
          >
            View PDF
          </button>
          <button
            type="button"
            className="secondary"
            onClick={() =>
              guardMonthThen(() =>
                download(
                  `/api/v1/reports/monthly.pdf?year=${year}&month=${month}`,
                  `monthly_${year}_${monthPad}.pdf`
                )
              )
            }
          >
            Download PDF
          </button>
          <button
            type="button"
            onClick={() =>
              guardMonthThen(() =>
                download(
                  `/api/v1/reports/monthly.xlsx?year=${year}&month=${month}`,
                  `EMS_Monthly_${year}_${monthPad}.xlsx`
                )
              )
            }
          >
            Download Excel
          </button>
          <button
            type="button"
            className="secondary"
            onClick={() =>
              guardMonthThen(() =>
                download(
                  `/api/v1/reports/monthly.csv?year=${year}&month=${month}`,
                  `monthly_${year}_${monthPad}.csv`
                )
              )
            }
          >
            Download CSV
          </button>
        </div>
      </div>

      {preview ? (
        <div className="card">
          <div className="toolbar" style={{ marginBottom: 12 }}>
            <h3 style={{ margin: 0, flex: 1 }}>{preview.title}</h3>
            <button type="button" className="secondary" onClick={() => setPreview(null)}>
              Close preview
            </button>
          </div>
          {preview.rows.length === 0 ? (
            <p className="muted">No rows for this period.</p>
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table>
                <thead>
                  <tr>
                    {preview.headers.map((h) => (
                      <th key={h}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {preview.rows.map((row, i) => (
                    <tr key={i}>
                      {row.map((cell, j) => (
                        <td key={j}>{cell}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      ) : null}
    </div>
  );
}
