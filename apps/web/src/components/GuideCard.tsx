import { useEffect, useMemo, useState } from "react";
import { createPortal } from "react-dom";
import { useLocation, useNavigate } from "react-router-dom";
import { MANAGER_DAY_GUIDE, MANAGER_GUIDE, STAFF_GUIDE } from "../guide/guideContent";
import {
  guidePathKey,
  guidesAllowedThisSession,
  markGuideSeen,
  skipGuidesThisSession,
  wasGuideSeen,
} from "../guide/guideStorage";

function staffDayPath() {
  const id = localStorage.getItem("ems_employee_id") || "";
  return id ? `/day/${id}` : "/projects";
}

function resolvePath(stepPath: string) {
  if (stepPath === "/day") return staffDayPath();
  return stepPath;
}

export function GuideCard({ manager }: { manager: boolean }) {
  const loc = useLocation();
  const nav = useNavigate();
  const [allowed, setAllowed] = useState(false);

  const steps = manager ? MANAGER_GUIDE : STAFF_GUIDE;
  const key = guidePathKey(loc.pathname);
  const index = steps.findIndex((s) => s.path === key);
  const step = index >= 0 ? steps[index] : manager && key === "/day" ? MANAGER_DAY_GUIDE : null;
  const visible = Boolean(allowed && step && !wasGuideSeen(key));

  const progress = useMemo(() => {
    if (index >= 0) return `${index + 1} of ${steps.length}`;
    if (step?.path === "/day") return "Day detail";
    return "";
  }, [index, step?.path, steps.length]);

  useEffect(() => {
    setAllowed(guidesAllowedThisSession());
  }, []);

  useEffect(() => {
    if (!visible) return;
    function onKey(e: KeyboardEvent) {
      if (e.key !== "Escape") return;
      if (document.querySelector(".modal-backdrop")) return;
      skipGuidesThisSession();
      setAllowed(false);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [visible]);

  if (!visible || !step) return null;

  function skip() {
    skipGuidesThisSession();
    setAllowed(false);
  }

  function next() {
    markGuideSeen(key);
    if (index >= 0) {
      const nxt = steps[index + 1];
      if (nxt) nav(resolvePath(nxt.path));
    }
  }

  const last = index < 0 || index >= steps.length - 1;

  return createPortal(
    <aside className="guide-card" role="dialog" aria-labelledby="guide-title" aria-describedby="guide-body">
      <p className="guide-kicker">Quick guide · {progress}</p>
      <h2 id="guide-title">{step.title}</h2>
      <p id="guide-body">{step.body}</p>
      <div className="guide-actions">
        <button type="button" className="secondary" onClick={skip}>
          Skip
        </button>
        <button type="button" onClick={next}>
          {last ? "Done" : "Next"}
        </button>
      </div>
    </aside>,
    document.body
  );
}
