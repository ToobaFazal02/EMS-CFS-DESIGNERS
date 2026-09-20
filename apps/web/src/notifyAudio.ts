/** Office alert chime — louder two-tone; unlock AudioContext after first user gesture (Desktop WebView2). */

let sharedCtx: AudioContext | null = null;
let unlocked = false;

function getCtx(): AudioContext | null {
  try {
    const AC = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
    if (!AC) return null;
    if (!sharedCtx) sharedCtx = new AC();
    return sharedCtx;
  } catch {
    return null;
  }
}

/** Call once on first click/tap so later notify beeps work in Tauri/Desktop. */
export function unlockNotifyAudio(): void {
  if (unlocked) return;
  const ctx = getCtx();
  if (!ctx) return;
  void ctx.resume().then(() => {
    unlocked = true;
  });
}

function tone(ctx: AudioContext, freq: number, start: number, dur: number, peak: number): void {
  const o = ctx.createOscillator();
  const g = ctx.createGain();
  o.type = "sine";
  o.frequency.value = freq;
  g.gain.setValueAtTime(0.0001, start);
  g.gain.exponentialRampToValueAtTime(peak, start + 0.02);
  g.gain.exponentialRampToValueAtTime(0.0001, start + dur);
  o.connect(g);
  g.connect(ctx.destination);
  o.start(start);
  o.stop(start + dur + 0.02);
}

/** Distinct office alert — two-note chime, audible on Desktop speakers. */
export function playNotifyChime(): void {
  try {
    const ctx = getCtx();
    if (!ctx) return;
    if (ctx.state === "suspended") void ctx.resume();
    const t0 = ctx.currentTime;
    tone(ctx, 880, t0, 0.16, 0.22);
    tone(ctx, 1174.7, t0 + 0.14, 0.22, 0.28);
  } catch {
    /* ignore */
  }
}

export function armNotifyAudioUnlock(): () => void {
  const onFirst = () => unlockNotifyAudio();
  window.addEventListener("pointerdown", onFirst, { once: true, capture: true });
  window.addEventListener("keydown", onFirst, { once: true, capture: true });
  return () => {
    window.removeEventListener("pointerdown", onFirst, true);
    window.removeEventListener("keydown", onFirst, true);
  };
}
