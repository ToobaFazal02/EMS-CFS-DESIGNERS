import { useEffect, useState } from "react";
import { applyTheme, getStoredTheme, type ThemeName } from "../theme";

function MoonIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M15.4 3.6A8.4 8.4 0 1019.2 17 6.8 6.8 0 0115.4 3.6z"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinejoin="round"
      />
      <path
        d="M9.2 6.2l.35 1.05L10.6 7.6l-1.05.35L9.2 9l-.35-1.05L7.8 7.6l1.05-.35L9.2 6.2zM17.6 11.4l.22.68.68.22-.68.22-.22.68-.22-.68-.68-.22.68-.22.22-.68z"
        fill="currentColor"
      />
    </svg>
  );
}

function SunIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden>
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

  function toggle() {
    const next: ThemeName = dark ? "light" : "dark";
    applyTheme(next);
    setTheme(next);
  }

  return (
    <div className={variant === "menu" ? "theme-switch-row theme-switch-row-menu" : "theme-switch-row"}>
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
