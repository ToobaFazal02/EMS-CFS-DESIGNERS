/** ISO 4217 → ISO 3166-1 alpha-2 for flagcdn.com (professional flag sprites). */
const SPECIAL: Record<string, string> = {
  EUR: "eu",
  GBP: "gb",
  USD: "us",
  AUD: "au",
  PKR: "pk",
  CAD: "ca",
  NZD: "nz",
  AED: "ae",
  SAR: "sa",
  SGD: "sg",
  CHF: "ch",
  JPY: "jp",
  CNY: "cn",
  INR: "in",
  MYR: "my",
  QAR: "qa",
  KWD: "kw",
  BHD: "bh",
  OMR: "om",
  ZAR: "za",
  HKD: "hk",
  KRW: "kr",
  MXN: "mx",
  BRL: "br",
  RUB: "ru",
  TRY: "tr",
  PLN: "pl",
  SEK: "se",
  NOK: "no",
  DKK: "dk",
  THB: "th",
  IDR: "id",
  PHP: "ph",
  VND: "vn",
  EGP: "eg",
  NGN: "ng",
  KES: "ke",
  ILS: "il",
  ARS: "ar",
  CLP: "cl",
  COP: "co",
  PEN: "pe",
  UAH: "ua",
  CZK: "cz",
  HUF: "hu",
  RON: "ro",
  BGN: "bg",
  HRK: "hr",
  ISK: "is",
  TWD: "tw",
  LKR: "lk",
  BDT: "bd",
  NPR: "np",
  AFN: "af",
  IQD: "iq",
  JOD: "jo",
  LBP: "lb",
  MAD: "ma",
  TND: "tn",
  DZD: "dz",
  GHS: "gh",
  UGX: "ug",
  TZS: "tz",
  ETB: "et",
  XAF: "cm",
  XOF: "sn",
  XCD: "ag",
};

export function flagCountryCode(currencyCode: string): string {
  const code = (currencyCode || "USD").trim().toUpperCase();
  if (SPECIAL[code]) return SPECIAL[code];
  if (code.length === 3) return code.slice(0, 2).toLowerCase();
  return "un";
}

/** flagcdn.com — verified CDN, 40px wide PNG flags. */
export function currencyFlagUrl(currencyCode: string, width = 40): string {
  const cc = flagCountryCode(currencyCode);
  return `https://flagcdn.com/w${width}/${cc}.png`;
}
