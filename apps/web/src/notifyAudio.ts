/** Soft alert chime — unlock AudioContext after first user gesture (Desktop WebView2). */

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

export function playNotifyChime(): void {
  try {
    const ctx = getCtx();
    if (!ctx) return;
    if (ctx.state === "suspended") void ctx.resume();
    const o = ctx.createOscillator();
    const g = ctx.createGain();
    o.type = "sine";
    o.frequency.value = 880;
    g.gain.value = 0.05;
    o.connect(g);
    g.connect(ctx.destination);
    o.start();
    g.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.2);
    o.stop(ctx.currentTime + 0.22);
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
