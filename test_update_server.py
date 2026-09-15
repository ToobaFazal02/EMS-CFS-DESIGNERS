"""
Mock update server for local Agent + Manager testing.
Run: python test_update_server.py
Agent / Manager point to http://localhost:9999 for version check.
"""
from flask import Flask, jsonify, send_file, abort
from pathlib import Path

app = Flask(__name__)

# Point these to your local test zips (build Agent, zip it, put path here)
AGENT_ZIP = Path(r"D:\imp\ems-cfs-designers\test-agent-1.1.3.zip")
MANAGER_SETUP = Path(r"D:\imp\ems-cfs-designers\apps\web\src-tauri\target\release\bundle\nsis\test-manager-0.1.3.exe")


@app.route("/api/v1/agent/version")
def version():
    """Mock version endpoint — returns higher version than current to trigger update banner."""
    return jsonify(
        {
            "agent_version": "1.1.3",  # Higher than 1.1.2 in code
            "agent_package_url": "http://localhost:9999/downloads/CFS-Agent-Install.zip",
            "download_url": "http://localhost:9999/downloads",
            "manager_version": "0.1.3",  # Higher than 0.1.2
            "manager_download_url": "http://localhost:9999/downloads/CFS-Designers-Manager-Setup.exe",
        }
    )


@app.route("/downloads/CFS-Agent-Install.zip")
def agent_package():
    if not AGENT_ZIP.exists():
        abort(
            404,
            description=f"Test Agent zip not found at {AGENT_ZIP}. Build Agent, zip dist folder, update AGENT_ZIP path.",
        )
    return send_file(AGENT_ZIP, mimetype="application/zip", as_attachment=True, download_name="CFS-Agent-Install.zip")


@app.route("/downloads/CFS-Designers-Manager-Setup.exe")
def manager_package():
    if not MANAGER_SETUP.exists():
        abort(
            404,
            description=f"Test Manager Setup not found at {MANAGER_SETUP}. Build Manager (tauri:build), update MANAGER_SETUP path.",
        )
    return send_file(
        MANAGER_SETUP, mimetype="application/octet-stream", as_attachment=True, download_name="CFS-Designers-Manager-Setup.exe"
    )


@app.route("/downloads")
def downloads_page():
    return """
    <h1>Test Downloads (mock)</h1>
    <ul>
      <li><a href="/downloads/CFS-Agent-Install.zip">CFS-Agent-Install.zip</a></li>
      <li><a href="/downloads/CFS-Designers-Manager-Setup.exe">CFS-Designers-Manager-Setup.exe</a></li>
    </ul>
    """


if __name__ == "__main__":
    print("=" * 60)
    print("Mock update server for Phase E local testing")
    print("=" * 60)
    print(f"Agent zip:     {AGENT_ZIP}")
    print(f"Manager Setup: {MANAGER_SETUP}")
    print("")
    print("Update these paths to your local test builds.")
    print("Then:")
    print("  1. Run this script: python test_update_server.py")
    print('  2. Agent: edit config.json → "api_base": "http://localhost:9999"')
    print("  3. Restart Agent → click Update → verify enroll stays")
    print("=" * 60)
    app.run(host="127.0.0.1", port=9999, debug=True)
