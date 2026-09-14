from __future__ import annotations

import json
import sqlite3
import sys
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import httpx


def app_root() -> Path:
    """Folder that holds config.json (next to the .exe when frozen)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def bundle_dir() -> Path:
    """Read-only files packed inside the .exe (icons)."""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", app_root()))
    return app_root()


ROOT = app_root()
CONFIG_PATH = ROOT / "config.json"
DATA_DIR = ROOT / "agent_data"
DB_PATH = DATA_DIR / "outbox.sqlite"


@dataclass
class Counters:
    lock: threading.Lock = field(default_factory=threading.Lock)
    mouse_clicks: int = 0
    key_presses: int = 0
    last_input_at: float = field(default_factory=time.time)

    def add_click(self) -> None:
        with self.lock:
            self.mouse_clicks += 1
            self.last_input_at = time.time()

    def add_key(self) -> None:
        with self.lock:
            self.key_presses += 1
            self.last_input_at = time.time()

    def drain(self) -> tuple[int, int, float]:
        with self.lock:
            c, k = self.mouse_clicks, self.key_presses
            self.mouse_clicks = 0
            self.key_presses = 0
            return c, k, self.last_input_at


DEFAULT_CONFIG = {
    "api_base": "http://127.0.0.1:8000",
    "device_token": "",
    "screenshot_interval_seconds": 180,
    "screenshot_blur": False,
    "screenshot_blur_radius": 2,
    "activity_interval_seconds": 15,
    "idle_seconds": 30,
    "auto_sign_out_idle_seconds": 1800,
    "auto_sign_out_on_sleep": True,
    "sleep_gap_seconds": 120,
    "employee_name": "",
    "employee_code": "",
}

# Keys that may be upgraded on install without wiping enroll / identity.
_POLICY_KEYS = (
    "screenshot_interval_seconds",
    "idle_seconds",
    "auto_sign_out_idle_seconds",
    "activity_interval_seconds",
    "auto_sign_out_on_sleep",
    "sleep_gap_seconds",
    "screenshot_blur",
    "screenshot_blur_radius",
)


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        bundled = bundle_dir() / "config.production.json"
        example = ROOT / "config.example.json"
        if bundled.is_file():
            CONFIG_PATH.write_text(bundled.read_text(encoding="utf-8"), encoding="utf-8")
        elif example.exists():
            CONFIG_PATH.write_text(example.read_text(encoding="utf-8"), encoding="utf-8")
        else:
            cfg0 = dict(DEFAULT_CONFIG)
            if getattr(sys, "frozen", False):
                cfg0["api_base"] = "https://ems.cfsdesigners.com"
            CONFIG_PATH.write_text(json.dumps(cfg0, indent=2), encoding="utf-8")
    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    for k, v in DEFAULT_CONFIG.items():
        cfg.setdefault(k, v)

    # Merge policy from shipped config.production.json (keeps device_token / name / code).
    # Fixes: reinstall kept idle=180 / screenshots=300 from an old config.json.
    changed = False
    prod_path = ROOT / "config.production.json"
    if not prod_path.is_file():
        prod_path = bundle_dir() / "config.production.json"
    if prod_path.is_file():
        try:
            prod = json.loads(prod_path.read_text(encoding="utf-8"))
            for k in _POLICY_KEYS:
                if k in prod and cfg.get(k) != prod[k]:
                    cfg[k] = prod[k]
                    changed = True
            # Production builds should always hit live API if still on localhost.
            if getattr(sys, "frozen", False):
                base = str(cfg.get("api_base") or "")
                if "127.0.0.1" in base or "localhost" in base:
                    cfg["api_base"] = str(prod.get("api_base") or "https://ems.cfsdesigners.com")
                    changed = True
        except Exception:
            pass
    if changed:
        save_config(cfg)
    return cfg


def save_config(cfg: dict) -> None:
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def init_outbox() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS outbox (
            id TEXT PRIMARY KEY,
            kind TEXT NOT NULL,
            payload TEXT NOT NULL,
            created_at TEXT NOT NULL,
            synced INTEGER DEFAULT 0
        )
        """
    )
    con.commit()
    con.close()


def enqueue(kind: str, payload: dict) -> str:
    oid = payload.get("id") or str(uuid.uuid4())
    payload["id"] = oid
    con = sqlite3.connect(DB_PATH)
    con.execute(
        "INSERT OR IGNORE INTO outbox(id, kind, payload, created_at, synced) VALUES (?,?,?,?,0)",
        (oid, kind, json.dumps(payload), datetime.now(timezone.utc).isoformat()),
    )
    con.commit()
    con.close()
    return oid


def pending_rows() -> list[tuple[str, str, str]]:
    con = sqlite3.connect(DB_PATH)
    rows = con.execute("SELECT id, kind, payload FROM outbox WHERE synced=0 ORDER BY created_at").fetchall()
    con.close()
    return rows


def mark_synced(oid: str) -> None:
    con = sqlite3.connect(DB_PATH)
    con.execute("UPDATE outbox SET synced=1 WHERE id=?", (oid,))
    con.commit()
    con.close()


class ApiClient:
    def __init__(self, base: str, token: str) -> None:
        self.base = base.rstrip("/")
        self.token = token

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    @staticmethod
    def _detail(r: httpx.Response) -> str:
        try:
            data = r.json()
            detail = data.get("detail")
            if isinstance(detail, str) and detail.strip():
                return detail.strip()
            if isinstance(detail, list) and detail:
                return str(detail[0])
        except Exception:
            pass
        if r.status_code == 400:
            return "Request was rejected. Check the values and try again."
        if r.status_code == 401:
            return "This PC is not authorized. Enroll again with a fresh code from the manager."
        if r.status_code >= 500:
            return "Server error. Try again in a moment."
        return f"Request failed (code {r.status_code})."

    def punch(self, payload: dict) -> tuple[bool, str]:
        r = httpx.post(f"{self.base}/api/v1/agent/punches", json=payload, headers=self._headers(), timeout=20)
        if r.status_code < 300:
            return True, ""
        return False, self._detail(r)

    def session_status(self) -> dict:
        r = httpx.get(f"{self.base}/api/v1/agent/session", headers=self._headers(), timeout=10)
        if r.status_code < 300:
            return r.json()
        return {"signed_in": False, "session_id": None}

    def activity(self, payload: dict) -> bool:
        r = httpx.post(f"{self.base}/api/v1/agent/activity", json=payload, headers=self._headers(), timeout=20)
        if r.status_code == 401:
            raise PermissionError(self._detail(r))  # caught by caller to trigger re-enroll
        return r.status_code < 300

    def screenshot(self, jpeg_bytes: bytes) -> bool:
        files = {"file": ("shot.jpg", jpeg_bytes, "image/jpeg")}
        r = httpx.post(
            f"{self.base}/api/v1/agent/screenshots",
            files=files,
            headers=self._headers(),
            timeout=60,
        )
        return r.status_code < 300

    def enroll(self, code: str, hostname: str) -> dict:
        url = f"{self.base}/api/v1/devices/enroll"
        try:
            r = httpx.post(
                url,
                json={"enroll_code": code, "hostname": hostname},
                timeout=12.0,
            )
        except httpx.TimeoutException as e:
            raise RuntimeError(
                "Server timed out while checking the enroll code.\n\n"
                "Check your internet, or ask the office if EMS is online.\n"
                f"Server: {self.base}"
            ) from e
        except httpx.ConnectError as e:
            raise RuntimeError(
                "Cannot reach the EMS server.\n\n"
                "Check your internet connection, then try again.\n"
                f"Server: {self.base}"
            ) from e
        except httpx.HTTPError as e:
            raise RuntimeError(
                f"Could not contact the EMS server ({e.__class__.__name__}).\n"
                f"Server: {self.base}"
            ) from e
        if r.status_code < 300:
            return r.json()
        detail = self._detail(r)
        # Map common API messages to client-friendly copy
        low = detail.lower()
        if "invalid" in low or "already used" in low or "not found" in low:
            raise RuntimeError(
                "Wrong enroll code (invalid or already used).\n\n"
                "Ask the manager to click Enroll PC / Re-enroll PC and paste the new code here."
            )
        if "employee" in low:
            raise RuntimeError("Employee record is missing. Ask the manager to check Employees.")
        raise RuntimeError(detail)
