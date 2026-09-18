use std::fs;
use std::process::Command;

use tauri::AppHandle;

/// Download Manager Setup.exe and run NSIS silent install (`/S`).
/// Spawns a detached PowerShell helper, then exits so files unlock.
/// Server DB / web data are never touched — only this PC's Manager binary.
#[tauri::command]
fn start_silent_manager_update(app: AppHandle, url: String) -> Result<(), String> {
  if url.trim().is_empty() || !(url.starts_with("https://") || url.starts_with("http://")) {
    return Err("Invalid update URL".into());
  }
  // Only allow our production downloads host (prevents drive-by URLs).
  let ok_host = url.contains("ems.cfsdesigners.com") || url.contains("localhost");
  if !ok_host {
    return Err("Update URL host not allowed".into());
  }

  let temp = std::env::temp_dir();
  let setup_path = temp.join("CFS-Designers-Manager-Setup.exe");
  let script_path = temp.join("cfs-manager-silent-update.ps1");

  let setup_ps = setup_path.to_string_lossy().replace('\'', "''");
  let url_ps = url.replace('\'', "''");

  let script = format!(
    r#"$ErrorActionPreference = 'Stop'
$url = '{url}'
$out = '{setup}'
Write-Output "Downloading Manager update..."
Invoke-WebRequest -Uri $url -OutFile $out -UseBasicParsing
# Wait for Manager process to exit (file locks)
for ($i = 0; $i -lt 60; $i++) {{
  $names = @('CFS Designers', 'app', 'cfs-designers')
  $alive = $false
  foreach ($n in $names) {{
    if (Get-Process -Name $n -ErrorAction SilentlyContinue) {{ $alive = $true }}
  }}
  if (-not $alive) {{ break }}
  Start-Sleep -Seconds 1
}}
Start-Sleep -Seconds 2
if (-not (Test-Path $out)) {{ throw 'Download missing' }}
# NSIS silent (currentUser install — no admin UAC in normal office installs)
Start-Process -FilePath $out -ArgumentList '/S' -Wait
# Relaunch from common Tauri currentUser locations
$candidates = @(
  (Join-Path $env:LOCALAPPDATA 'CFS Designers\CFS Designers.exe'),
  (Join-Path $env:LOCALAPPDATA 'com.cfsdesigners.ems\CFS Designers.exe')
)
foreach ($exe in $candidates) {{
  if (Test-Path $exe) {{
    Start-Process -FilePath $exe
    break
  }}
}}
"#,
    url = url_ps,
    setup = setup_ps
  );

  fs::write(&script_path, script).map_err(|e| format!("Could not write updater script: {e}"))?;

  #[cfg(windows)]
  {
    use std::os::windows::process::CommandExt;
    const CREATE_NO_WINDOW: u32 = 0x08000000;
    const DETACHED_PROCESS: u32 = 0x00000008;
    Command::new("powershell")
      .args([
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-WindowStyle",
        "Hidden",
        "-File",
        script_path.to_string_lossy().as_ref(),
      ])
      .creation_flags(CREATE_NO_WINDOW | DETACHED_PROCESS)
      .spawn()
      .map_err(|e| format!("Could not start updater: {e}"))?;
  }

  #[cfg(not(windows))]
  {
    return Err("Silent Manager update is Windows-only".into());
  }

  // Exit so NSIS can replace binaries
  app.exit(0);
  Ok(())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
  tauri::Builder::default()
    .setup(|app| {
      if cfg!(debug_assertions) {
        app.handle().plugin(
          tauri_plugin_log::Builder::default()
            .level(log::LevelFilter::Info)
            .build(),
        )?;
      }
      Ok(())
    })
    .invoke_handler(tauri::generate_handler![start_silent_manager_update])
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}
