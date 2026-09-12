import { useEffect, useState } from "react";
import { resolveUrl } from "../api";

export function AuthedImg({
  path,
  className,
  alt,
  audit = false,
}: {
  path: string;
  className?: string;
  alt: string;
  /** When true, server writes screenshot_view audit (day lightbox only). */
  audit?: boolean;
}) {
  const [src, setSrc] = useState("");
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    let url = "";
    let cancelled = false;
    setSrc("");
    setFailed(false);
    const token = localStorage.getItem("ems_token") || "";
    const clean = resolveUrl(path.split("?")[0]);
    const fetchPath = audit ? `${clean}${clean.includes("?") ? "&" : "?"}audit=1` : clean;
    fetch(fetchPath, { headers: { Authorization: `Bearer ${token}` }, cache: "no-store" })
      .then((r) => {
        if (!r.ok) throw new Error("img");
        return r.blob();
      })
      .then((b) => {
        if (cancelled) return;
        if (!b || b.size < 32) throw new Error("empty");
        url = URL.createObjectURL(b);
        setSrc(url);
      })
      .catch(() => {
        if (!cancelled) {
          setFailed(true);
          setSrc("");
        }
      });
    return () => {
      cancelled = true;
      if (url) URL.revokeObjectURL(url);
    };
  }, [path, audit]);
  if (failed) {
    return (
      <div className={`${className || ""} thumb-empty`} role="img" aria-label="Screenshot unavailable">
        <span>Unavailable</span>
        <small>Could not load this capture</small>
      </div>
    );
  }
  if (!src) {
    return (
      <div className={`${className || ""} thumb-empty`} role="img" aria-label="Loading screenshot">
        <span>Loading…</span>
      </div>
    );
  }
  return <img className={className} src={src} alt={alt} />;
}
