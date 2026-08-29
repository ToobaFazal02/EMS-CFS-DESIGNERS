import { useEffect, useRef } from "react";

/** CSS 3D steel stage — perspective slabs + mouse parallax; CFS only. */
export function LoginStage3D() {
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const root = rootRef.current;
    if (!root) return;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce) return;

    const onMove = (e: MouseEvent) => {
      const rect = root.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / Math.max(rect.width, 1) - 0.5) * 2;
      const y = ((e.clientY - rect.top) / Math.max(rect.height, 1) - 0.5) * 2;
      root.style.setProperty("--mx", String(Math.max(-1, Math.min(1, x))));
      root.style.setProperty("--my", String(Math.max(-1, Math.min(1, y))));
    };
    window.addEventListener("mousemove", onMove, { passive: true });
    return () => window.removeEventListener("mousemove", onMove);
  }, []);

  return (
    <div className="login-stage" ref={rootRef} aria-hidden>
      <div className="login-stage-glow" />
      <div className="login-stage-floor" />
      <div className="login-scene">
        <div className="steel-stack">
          <div className="steel-slab slab-back">
            <span className="slab-face slab-front" />
            <span className="slab-face slab-right" />
            <span className="slab-face slab-bottom" />
            <span className="slab-shine" />
          </div>
          <div className="steel-slab slab-mid">
            <span className="slab-face slab-front">
              <span className="slab-rivet" />
              <span className="slab-rivet" />
              <span className="slab-rivet" />
              <span className="slab-rivet" />
              <span className="slab-groove" />
            </span>
            <span className="slab-face slab-right" />
            <span className="slab-face slab-bottom" />
          </div>
          <div className="steel-slab slab-front-card">
            <span className="slab-face slab-front">
              <span className="slab-mark">CFS</span>
            </span>
            <span className="slab-face slab-right" />
            <span className="slab-face slab-bottom" />
          </div>
        </div>
        <div className="orbit orbit-1" />
        <div className="orbit orbit-2" />
        <div className="gold-beam" />
        <div className="gold-spark spark-a" />
        <div className="gold-spark spark-b" />
        <div className="gold-spark spark-c" />
      </div>
    </div>
  );
}
