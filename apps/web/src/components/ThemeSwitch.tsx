import { useEffect, useState } from "react";
import { applyTheme, getStoredTheme, type ThemeName } from "../theme";

function MoonIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M15.5 3.5A8.5 8.5 0 1019 16.7 7 7 0 0115.5 3.5z"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function SunIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden>
      <circle cx="12" cy="12" r="4.2" stroke="currentColor" strokeWidth="1.8" />
      <path
        d="M12 3v1.6M12 19.4V21M4.2 12H2.6M21.4 12h-1.6M6.1 6.1l1.1 1.1M16.8 16.8l1.1 1.1M6.1 17.9l1.1-1.1M16.8 7.2l1.1-1.1"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
      />
    </svg>
  );
}

export function ThemeSwitch({ variant = "page" }: { variant?: "page" | "menu" }) {
  const [theme, setTheme] = useState<ThemeName>(() => getStoredTheme());

  useEffect(() => {
    const sync = () => setTheme(getStoredTheme());
    window.addEventListener("ems-theme", sync);
    return () => window.removeEventListener("ems-theme", sync);
  }, []);

  function choose(next: ThemeName) {
    applyTheme(next);
    setTheme(next);
  }

  return (
    <div
      className={variant === "menu" ? "theme-icons theme-icons-menu" : "theme-icons"}
      role="group"
      aria-label="Colour theme"
    >
      <button
        type="button"
        className={theme === "dark" ? "theme-icon-btn is-on" : "theme-icon-btn"}
        aria-pressed={theme === "dark"}
        aria-label="Dark mode"
        title="Dark mode"
        onClick={() => choose("dark")}
      >
        <MoonIcon />
      </button>
      <button
        type="button"
        className={theme === "light" ? "theme-icon-btn is-on" : "theme-icon-btn"}
        aria-pressed={theme === "light"}
        aria-label="Light mode"
        title="Light mode"
        onClick={() => choose("light")}
      >
        <SunIcon />
      </button>
    </div>
  );
}
