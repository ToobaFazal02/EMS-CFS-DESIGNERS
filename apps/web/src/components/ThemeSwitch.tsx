import { useEffect, useState } from "react";
import { applyTheme, getStoredTheme, type ThemeName } from "../theme";

function MoonIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M15.4 3.6A8.4 8.4 0 1019.2 17 6.8 6.8 0 0115.4 3.6z"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function SunIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden>
      <circle cx="12" cy="12" r="3.6" stroke="currentColor" strokeWidth="1.7" />
      <path
        d="M12 3.2v1.5M12 19.3v1.5M4.7 12H3.2M20.8 12h-1.5M6.4 6.4l1.05 1.05M16.55 16.55l1.05 1.05M6.4 17.6l1.05-1.05M16.55 7.45l1.05-1.05"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
      />
    </svg>
  );
}

export function ThemeSwitch({
  variant = "page",
  showLabel = false,
}: {
  variant?: "page" | "menu";
  showLabel?: boolean;
}) {
  const [theme, setTheme] = useState<ThemeName>(() => getStoredTheme());

  useEffect(() => {
    const sync = () => setTheme(getStoredTheme());
    window.addEventListener("ems-theme", sync);
    return () => window.removeEventListener("ems-theme", sync);
  }, []);

  const dark = theme === "dark";

  function setMode(next: ThemeName) {
    applyTheme(next);
    setTheme(next);
  }

  if (variant === "menu") {
    return (
      <div className="theme-seg" role="group" aria-label="Theme">
        <p className="theme-seg-label">Theme</p>
        <div className="theme-seg-track">
          <button
            type="button"
            className={`theme-seg-btn${dark ? " is-active" : ""}`}
            aria-pressed={dark}
            onClick={() => setMode("dark")}
          >
            <MoonIcon /> Dark
          </button>
          <button
            type="button"
            className={`theme-seg-btn${!dark ? " is-active" : ""}`}
            aria-pressed={!dark}
            onClick={() => setMode("light")}
          >
            <SunIcon /> Light
          </button>
        </div>
      </div>
    );
  }

  function toggle() {
    setMode(dark ? "light" : "dark");
  }

  return (
    <div className="theme-switch-row">
      {showLabel ? <span className="theme-switch-copy">Dark mode</span> : null}
      <button
        type="button"
        className={dark ? "theme-switch is-dark" : "theme-switch is-light"}
        role="switch"
        aria-checked={dark}
        aria-label={dark ? "Dark mode on, switch to light" : "Light mode on, switch to dark"}
        title={dark ? "Dark mode" : "Light mode"}
        onClick={toggle}
      >
        <span className="theme-switch-ico theme-switch-sun" aria-hidden>
          <SunIcon />
        </span>
        <span className="theme-switch-knob" aria-hidden />
        <span className="theme-switch-ico theme-switch-moon" aria-hidden>
          <MoonIcon />
        </span>
      </button>
    </div>
  );
}
