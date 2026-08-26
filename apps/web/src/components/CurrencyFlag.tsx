import { currencyFlagUrl } from "./currencyFlags";

type Props = {
  currencyCode: string;
  size?: "sm" | "md";
  className?: string;
};

export function CurrencyFlag({ currencyCode, size = "sm", className = "" }: Props) {
  const w = size === "md" ? 48 : 40;
  const cc = (currencyCode || "USD").toUpperCase();
  return (
    <img
      className={`currency-flag currency-flag-${size}${className ? ` ${className}` : ""}`}
      src={currencyFlagUrl(cc, w)}
      width={size === "md" ? 24 : 20}
      height={size === "md" ? 18 : 15}
      alt=""
      loading="lazy"
      decoding="async"
    />
  );
}
