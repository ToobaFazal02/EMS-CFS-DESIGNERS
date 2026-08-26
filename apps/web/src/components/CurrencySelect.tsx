import { useEffect, useId, useMemo, useRef, useState } from "react";
import { CurrencyFlag } from "./CurrencyFlag";
import { filterCurrencies, getCurrency, normalizeCurrencyCode, type CurrencyOption } from "./currencies";

type Props = {
  value: string;
  onChange: (code: string) => void;
  required?: boolean;
  disabled?: boolean;
  id?: string;
};

export function CurrencySelect({ value, onChange, required, disabled, id }: Props) {
  const autoId = useId();
  const inputId = id || autoId;
  const rootRef = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [highlight, setHighlight] = useState(0);

  const selected = useMemo(() => getCurrency(value), [value]);
  const options = useMemo(() => filterCurrencies(open ? query : value, 60), [open, query, value]);

  useEffect(() => {
    function onDoc(e: MouseEvent) {
      if (!rootRef.current?.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  useEffect(() => {
    setHighlight(0);
  }, [query, open]);

  function pick(option: CurrencyOption) {
    onChange(option.code);
    setQuery("");
    setOpen(false);
  }

  function commitQuery() {
    const code = normalizeCurrencyCode(query || value);
    onChange(code);
    setQuery("");
    setOpen(false);
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      if (!open) setOpen(true);
      else setHighlight((i) => Math.min(i + 1, options.length - 1));
      return;
    }
    if (e.key === "ArrowUp") {
      e.preventDefault();
      setHighlight((i) => Math.max(i - 1, 0));
      return;
    }
    if (e.key === "Enter") {
      e.preventDefault();
      if (open && options[highlight]) pick(options[highlight]);
      else commitQuery();
      return;
    }
    if (e.key === "Escape") {
      setOpen(false);
      setQuery("");
    }
  }

  const code = selected?.code || normalizeCurrencyCode(value);
  const displayValue = open ? query : code;

  return (
    <div className={`currency-select${open ? " is-open" : ""}`} ref={rootRef}>
      {!open ? <CurrencyFlag currencyCode={code} className="currency-select-flag" /> : null}
      <input
        id={inputId}
        type="text"
        className={`currency-select-input${open ? "" : " currency-select-input-closed"}`}
        value={displayValue}
        required={required}
        disabled={disabled}
        autoComplete="off"
        spellCheck={false}
        placeholder="USD"
        title={selected?.name || code}
        onFocus={() => {
          setOpen(true);
          setQuery("");
        }}
        onChange={(e) => {
          setQuery(e.target.value);
          setOpen(true);
        }}
        onBlur={() => {
          window.setTimeout(() => {
            if (!rootRef.current?.contains(document.activeElement)) {
              if (query.trim()) commitQuery();
              setOpen(false);
              setQuery("");
            }
          }, 120);
        }}
        onKeyDown={onKeyDown}
        aria-expanded={open}
        aria-controls={`${inputId}-listbox`}
        aria-autocomplete="list"
        role="combobox"
      />
      <button
        type="button"
        className="currency-select-toggle"
        tabIndex={-1}
        disabled={disabled}
        aria-label="Show currencies"
        onMouseDown={(e) => e.preventDefault()}
        onClick={() => setOpen((v) => !v)}
      >
        ▾
      </button>
      {open ? (
        <ul className="currency-select-menu" id={`${inputId}-listbox`} role="listbox">
          {options.map((opt, i) => (
            <li key={opt.code}>
              <button
                type="button"
                role="option"
                aria-selected={opt.code === value}
                title={opt.name}
                className={`currency-select-option${i === highlight ? " is-active" : ""}${opt.code === value ? " is-selected" : ""}`}
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => pick(opt)}
              >
                <CurrencyFlag currencyCode={opt.code} size="md" className="currency-option-flag" />
                <span className="currency-select-code">{opt.code}</span>
              </button>
            </li>
          ))}
          {!options.length ? <li className="currency-select-empty">No match</li> : null}
        </ul>
      ) : null}
    </div>
  );
}
