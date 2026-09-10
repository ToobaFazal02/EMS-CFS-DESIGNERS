import { useEffect, useRef, useState } from "react";

const PRESETS: { hex: string; label: string }[] = [
  { hex: "#FFFF00", label: "Yellow" },
  { hex: "#7A1F2E", label: "Maroon" },
  { hex: "#92D050", label: "Green" },
  { hex: "#C9A227", label: "Gold" },
  { hex: "#AED6F1", label: "Blue" },
];

type Props = {
  label: string;
  value?: string;
  onChange: (hex: string) => void;
};

/** Compact cell background picker — presets + custom + clear. */
export function CellColorPicker({ label, value, onChange }: Props) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const hex = (value || "").trim();

  useEffect(() => {
    if (!open) return;
    function onDoc(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [open]);

  return (
    <div className="cell-color-picker" ref={ref}>
      <button
        type="button"
        className={`cell-color-btn${hex ? " has-color" : ""}`}
        title={`${label} cell color`}
        aria-label={`${label} cell color`}
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
        style={hex ? { background: hex } : undefined}
      />
      {open ? (
        <div className="cell-color-menu" role="dialog" aria-label={`${label} color`}>
          <p className="cell-color-menu-title">{label}</p>
          <div className="cell-color-presets">
            {PRESETS.map((p) => (
              <button
                key={p.hex}
                type="button"
                className={`cell-color-swatch${hex.toUpperCase() === p.hex ? " is-active" : ""}`}
                style={{ background: p.hex }}
                title={p.label}
                aria-label={p.label}
                onClick={() => {
                  onChange(p.hex);
                  setOpen(false);
                }}
              />
            ))}
            <label className="cell-color-custom" title="Custom color">
              <input
                type="color"
                value={hex && /^#[0-9A-Fa-f]{6}$/.test(hex) ? hex : "#FFFF00"}
                onChange={(e) => onChange(e.target.value.toUpperCase())}
              />
            </label>
            <button
              type="button"
              className="cell-color-clear"
              onClick={() => {
                onChange("");
                setOpen(false);
              }}
            >
              Clear
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
