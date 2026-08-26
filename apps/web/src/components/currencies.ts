export type CurrencyOption = {
  code: string;
  name: string;
  search: string;
};

const COMMON_CODES = [
  "USD",
  "AUD",
  "PKR",
  "EUR",
  "GBP",
  "CAD",
  "NZD",
  "AED",
  "SAR",
  "SGD",
  "CHF",
  "JPY",
  "CNY",
  "INR",
  "MYR",
  "QAR",
  "KWD",
  "BHD",
  "OMR",
  "ZAR",
];

const ALIAS: Record<string, string[]> = {
  USD: ["u", "us", "usa", "dollar", "dollars", "american", "united states"],
  AUD: ["au", "aus", "australia", "australian", "australian dollar"],
  PKR: ["pk", "pakistan", "pakistani", "rupee", "rupiya"],
  EUR: ["eu", "euro", "europe", "european"],
  GBP: ["gb", "uk", "pound", "british", "sterling", "england"],
  CAD: ["ca", "canada", "canadian"],
  NZD: ["nz", "new zealand", "kiwi"],
  AED: ["ae", "uae", "emirates", "dirham", "dubai"],
  SAR: ["sa", "saudi", "riyal"],
  SGD: ["sg", "singapore"],
  CHF: ["swiss", "franc", "switzerland"],
  JPY: ["jp", "japan", "yen"],
  CNY: ["cn", "china", "yuan", "rmb"],
  INR: ["in", "india", "indian"],
  MYR: ["my", "malaysia", "ringgit"],
  QAR: ["qa", "qatar"],
  KWD: ["kw", "kuwait"],
  BHD: ["bh", "bahrain"],
  OMR: ["om", "oman"],
  ZAR: ["za", "south africa", "rand"],
};

const LOCATION_CURRENCY: [RegExp, string][] = [
  [/\b(us|usa|united states|america)\b/i, "USD"],
  [/\b(australia|aus|au)\b/i, "AUD"],
  [/\b(pakistan|pk)\b/i, "PKR"],
  [/\b(united kingdom|uk|britain|england|gb)\b/i, "GBP"],
  [/\b(canada|ca)\b/i, "CAD"],
  [/\b(new zealand|nz)\b/i, "NZD"],
  [/\b(uae|dubai|emirates|ae)\b/i, "AED"],
  [/\b(saudi|ksa)\b/i, "SAR"],
  [/\b(singapore|sg)\b/i, "SGD"],
  [/\b(europe|eu|germany|france|italy|spain|netherlands)\b/i, "EUR"],
  [/\b(india|in)\b/i, "INR"],
  [/\b(malaysia|my)\b/i, "MYR"],
  [/\b(qatar|qa)\b/i, "QAR"],
  [/\b(kuwait|kw)\b/i, "KWD"],
  [/\b(bahrain|bh)\b/i, "BHD"],
  [/\b(oman|om)\b/i, "OMR"],
  [/\b(south africa|za)\b/i, "ZAR"],
  [/\b(japan|jp)\b/i, "JPY"],
  [/\b(china|cn)\b/i, "CNY"],
  [/\b(switzerland|ch)\b/i, "CHF"],
];

let cached: CurrencyOption[] | null = null;
let displayNames: Intl.DisplayNames | null = null;

function currencyName(code: string): string {
  try {
    if (!displayNames) displayNames = new Intl.DisplayNames(["en"], { type: "currency" });
    return displayNames.of(code) || code;
  } catch {
    return code;
  }
}

function buildSearchText(code: string, name: string): string {
  const aliases = ALIAS[code] || [];
  return [code, name, ...aliases].join(" ").toLowerCase();
}

export function listCurrencies(): CurrencyOption[] {
  if (cached) return cached;
  let codes: string[] = COMMON_CODES;
  try {
    codes = Intl.supportedValuesOf("currency");
  } catch {
    /* older runtime */
  }
  const uniq = Array.from(new Set(codes.map((c) => c.toUpperCase())));
  cached = uniq
    .map((code) => {
      const name = currencyName(code);
      return { code, name, search: buildSearchText(code, name) };
    })
    .sort((a, b) => a.code.localeCompare(b.code));
  return cached;
}

export function getCurrency(code: string): CurrencyOption | undefined {
  const c = normalizeCurrencyCode(code);
  return listCurrencies().find((x) => x.code === c);
}

export function normalizeCurrencyCode(raw: string): string {
  const q = (raw || "").trim().toUpperCase();
  if (/^[A-Z]{3}$/.test(q)) return q;
  const lower = (raw || "").trim().toLowerCase();
  if (!lower) return "USD";
  for (const [code, aliases] of Object.entries(ALIAS)) {
    if (aliases.some((a) => a === lower || a.startsWith(lower) || lower.startsWith(a))) return code;
  }
  const match = filterCurrencies(lower, 1)[0];
  return match?.code || "USD";
}

export function filterCurrencies(query: string, limit = 80): CurrencyOption[] {
  const all = listCurrencies();
  const q = query.trim().toLowerCase();
  if (!q) {
    const common = COMMON_CODES.map((code) => all.find((c) => c.code === code)).filter(Boolean) as CurrencyOption[];
    const rest = all.filter((c) => !COMMON_CODES.includes(c.code));
    return [...common, ...rest].slice(0, limit);
  }

  const scored = all
    .map((c) => {
      let score = 0;
      const code = c.code.toLowerCase();
      if (code === q) score = 1000;
      else if (code.startsWith(q)) score = 900 - (code.length - q.length);
      else if (c.search.includes(q)) score = 500;
      else {
        for (const [aliasCode, aliases] of Object.entries(ALIAS)) {
          if (aliasCode !== c.code) continue;
          if (aliases.some((a) => a === q || a.startsWith(q))) {
            score = 850;
            break;
          }
        }
      }
      return { c, score };
    })
    .filter((x) => x.score > 0)
    .sort((a, b) => b.score - a.score || a.c.code.localeCompare(b.c.code));

  return scored.slice(0, limit).map((x) => x.c);
}

export function guessCurrencyFromLocation(location: string): string {
  const loc = (location || "").trim();
  if (!loc) return "USD";
  for (const [re, code] of LOCATION_CURRENCY) {
    if (re.test(loc)) return code;
  }
  return "USD";
}

export function formatMoney(amount: number, currency: string): string {
  const code = normalizeCurrencyCode(currency);
  try {
    return new Intl.NumberFormat("en", { style: "currency", currency: code }).format(amount);
  } catch {
    return `${code} ${Number(amount).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  }
}
