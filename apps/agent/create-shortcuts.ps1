# Creates Desktop, Start Menu, and Startup shortcuts. ASCII only.
param(
    [Parameter(Mandatory = $true)][string]$Python,
    [Parameter(Mandatory = $true)][string]$WorkDir,
    [string]$Icon = "",
    [Parameter(Mandatory = $true)][string]$StartupLink,
    [Parameter(Mandatory = $true)][string]$MenuLink,
    [Parameter(Mandatory = $true)][string]$DesktopLink,
    [string]$Arguments = "-m ems_agent"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $Python)) {
    throw "Python not found: $Python"
}
$pyw = Join-Path (Split-Path -Parent $Python) "pythonw.exe"
if (Test-Path -LiteralPath $pyw) {
    $Python = $pyw
}
if (-not (Test-Path -LiteralPath $WorkDir)) {
    throw "Work folder not found: $WorkDir"
}

$ws = New-Object -ComObject WScript.Shell
foreach ($path in @($StartupLink, $MenuLink, $DesktopLink)) {
    $dir = Split-Path -Parent $path
    if ($dir -and -not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    $s = $ws.CreateShortcut($path)
    $s.TargetPath = $Python
    $s.Arguments = $(if ($Arguments -eq "NONE") { "" } else { $Arguments })
    $s.WorkingDirectory = $WorkDir
    $s.WindowStyle = 7
    $s.Description = "CFS Designers Agent"
    if ($Icon -and (Test-Path -LiteralPath $Icon)) {
        $s.IconLocation = $Icon
    }
    $s.Save()
}

Write-Host "SHORTCUTS_OK"
