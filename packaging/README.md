# Packaging — Agent installer

## Pilot (no Inno needed)

Copy `apps/agent` to the employee PC and run **`INSTALL-AGENT.bat`**.

## Optional `.exe` (later)

1. Install [Inno Setup 6](https://jrsoftware.org/isinfo.php)
2. Prepare `packaging/agent-dist/` with the agent files you want shipped (exclude huge caches)
3. Compile `packaging/agent-installer.iss`
4. Deliver `packaging/Output/CFS-Designers-Agent-Setup.exe`

Not required for your current E2E test of the office platform.
