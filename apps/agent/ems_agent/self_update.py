"""
Click-to-update for Employee Agent (frozen PyInstaller build).

Flow (Chrome-like, safe for enroll data):
1. Download CFS-Agent-Install.zip from API package URL (background thread).
2. Extract to a staging folder under %TEMP%.
3. Write APPLY-UPDATE.ps1 that waits for this process to exit, then
   copies new files over the install dir WITHOUT replacing config.json
   or deleting agent_data/ (enroll + offline queue stay).
4. Launch the script detached, then exit the Agent so files unlock.

Server DB is never touched. Only local Program Files / install folder binaries change.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from ems_agent.storage import app_root


def _find_package_root(extract_dir: Path) -> Path:
    """Locate folder that contains CFS-Designers-Agent.exe after unzip."""
    direct = extract_dir / "CFS-Designers-Agent.exe"
    if direct.is_file():
        return extract_dir
    nested = extract_dir / "CFS-Designers-Agent" / "CFS-Designers-Agent.exe"
    if nested.is_file():
        return nested.parent
    for p in extract_dir.rglob("CFS-Designers-Agent.exe"):
        return p.parent
    raise FileNotFoundError(
        "Downloaded zip does not contain CFS-Designers-Agent.exe. Re-upload Agent zip on server."
    )


def _write_apply_script(
    *,
    install_dir: Path,
    staging_dir: Path,
    exe_name: str = "CFS-Designers-Agent.exe",
) -> Path:
    """PowerShell: wait for Agent exit → robocopy (keep config + agent_data) → relaunch."""
    script = Path(tempfile.gettempdir()) / "cfs-agent-apply-update.ps1"
    # Escape for single-quoted PowerShell strings
    inst = str(install_dir).replace("'", "''")
    stag = str(staging_dir).replace("'", "''")
    body = f"""$ErrorActionPreference = 'Stop'
$install = '{inst}'
$staging = '{stag}'
$exeName = '{exe_name}'
$exePath = Join-Path $install $exeName

# Wait until Agent process exits (file locks clear)
for ($i = 0; $i -lt 90; $i++) {{
  $procs = Get-Process -Name 'CFS-Designers-Agent' -ErrorAction SilentlyContinue
  if (-not $procs) {{ break }}
  Start-Sleep -Seconds 1
}}
Start-Sleep -Seconds 1

if (-not (Test-Path (Join-Path $staging $exeName))) {{
  throw "Staging package missing $exeName"
}}

# Merge new binaries; never mirror-delete (keeps agent_data). Never overwrite config.json.
& robocopy $staging $install /E /XF config.json /R:2 /W:1 /NFL /NDL /NJH /NJS /NP | Out-Null
$rc = $LASTEXITCODE
# robocopy 0-7 = success-ish
if ($rc -ge 8) {{ throw "robocopy failed with code $rc" }}

if (Test-Path $exePath) {{
  Start-Process -FilePath $exePath -WorkingDirectory $install
}}

# Cleanup staging (best-effort)
try {{ Remove-Item -LiteralPath $staging -Recurse -Force -ErrorAction SilentlyContinue }} catch {{}}
"""
    script.write_text(body, encoding="utf-8")
    return script


def download_and_stage(package_url: str, on_progress=None) -> Path:
    """
    Download zip to temp and extract. Returns staging dir with Agent exe.
    on_progress(fraction 0..1 | None, message) optional.
    """
    import httpx

    if on_progress:
        on_progress(0.02, "Downloading update…")

    tmp_root = Path(tempfile.mkdtemp(prefix="cfs-agent-upd-"))
    zip_path = tmp_root / "CFS-Agent-Install.zip"
    extract_dir = tmp_root / "extract"
    extract_dir.mkdir(parents=True, exist_ok=True)

    with httpx.stream("GET", package_url, follow_redirects=True, timeout=300.0) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length") or 0)
        done = 0
        with open(zip_path, "wb") as f:
            for chunk in r.iter_bytes(1024 * 64):
                f.write(chunk)
                done += len(chunk)
                if on_progress and total > 0:
                    on_progress(min(0.85, 0.05 + 0.8 * (done / total)), "Downloading update…")

    if on_progress:
        on_progress(0.88, "Extracting…")

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_dir)

    staging = _find_package_root(extract_dir)
    if on_progress:
        on_progress(0.95, "Preparing install…")
    return staging


def apply_update_and_exit(package_url: str, on_progress=None) -> None:
    """
    Download, stage, spawn apply script, then terminate this process.
    Call from a worker thread; use signals to update UI; exit on main thread after return prep.
    Raises on failure (caller shows error; Agent keeps running).
    """
    if not getattr(sys, "frozen", False):
        raise RuntimeError("Background update only works from the installed Agent exe (not Python source).")

    install_dir = app_root()
    staging = download_and_stage(package_url, on_progress=on_progress)
    script = _write_apply_script(install_dir=install_dir, staging_dir=staging)

    # Detached PowerShell (no console window)
    creationflags = 0
    if sys.platform == "win32":
        creationflags = subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS  # type: ignore[attr-defined]

    subprocess.Popen(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-WindowStyle",
            "Hidden",
            "-File",
            str(script),
        ],
        cwd=str(install_dir),
        close_fds=True,
        creationflags=creationflags,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    if on_progress:
        on_progress(1.0, "Restarting Agent…")
