# Signed Tauri updater — ops (P3)

**Status:** Checklist ready. Click→silent Setup MVP remains production path until signing keys exist.

## Why not flip the switch in this PR?

Tauri’s official updater **requires** Ed25519 signatures ([docs](https://v2.tauri.app/plugin/updater/)). Without a private key in CI, builds cannot ship `.sig` files. Losing the private key bricks updates for installed clients.

## Steps (office / DevOps)

1. `npm run tauri -- signer generate -w ./secrets/ems-updater.key` (store offline + password manager).
2. Add public key to `apps/web/src-tauri/tauri.conf.json` under `plugins.updater`.
3. GitHub Actions secret `TAURI_SIGNING_PRIVATE_KEY` (+ `TAURI_SIGNING_PRIVATE_KEY_PASSWORD`).
4. Enable `createUpdaterArtifacts: true` on NSIS bundle.
5. Host `https://ems.cfsdesigners.com/downloads/updater/latest.json`.
6. Set `installMode` to `passive` for currentUser NSIS installs.
7. Smoke: old Setup → banner → install → relaunch at new version.

## Current MVP (already in Manager 0.1.6+)

- Poll `/api/v1/agent/version` for `manager_version`
- `start_silent_manager_update` downloads Setup.exe + `/S`
- Fallback `open_external_url` if silent path fails
