import { currencyFlagUrl } from "./currencyFlags";

type Props = {
  currencyCode: string;
  size?: "sm" | "md";
  className?: string;
};

export function CurrencyFlag({ currencyCode, size = "sm", className = "" }: Props) {
  // flagcdn.com only supports w20, w40, w80 etc. — never w48
  const urlW = size === "md" ? 40 : 20;
  const displayW = size === "md" ? 22 : 18;
  const displayH = size === "md" ? 16 : 13;
  const cc = (currencyCode || "USD").toUpperCase();
  return (
    <img
      className={`currency-flag currency-flag-${size}${className ? ` ${className}` : ""}`}
      src={currencyFlagUrl(cc, urlW)}
      width={displayW}
      height={displayH}
      alt=""
      loading="lazy"
      decoding="async"
    />
  );
}
