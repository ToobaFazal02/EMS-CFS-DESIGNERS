/**
 * P3 — Signed Tauri updater polish (ops checklist).
 *
 * Current Desktop path (shipped): click → `start_silent_manager_update` downloads
 * Setup.exe from ems.cfsdesigners.com and runs NSIS `/S` (Phase E MVP).
 *
 * Professional signed updater (`@tauri-apps/plugin-updater`) needs keys + CI:
 * https://v2.tauri.app/plugin/updater/
 *
 * ## When ready to enable signed updates
 *
 * 1. Generate keys once (never commit private key):
 *    `npm run tauri -- signer generate -w ~/.tauri/ems.key`
 * 2. Put public key in `tauri.conf.json` → `plugins.updater.pubkey`
 * 3. CI secret: `TAURI_SIGNING_PRIVATE_KEY` (+ password if set)
 * 4. Set `bundle.createUpdaterArtifacts: true`
 * 5. Publish `latest.json` + `.nsis.zip` + `.sig` to `/downloads/updater/`
 * 6. Prefer Windows `installMode: "passive"` for per-user installs
 *
 * Until keys exist in office CI, keep the silent Setup download path
 * (`ManagerUpdateBanner` + `open_external_url` fallback).
 */

export const UPDATER_MODE = "silent-setup-mvp" as const;
