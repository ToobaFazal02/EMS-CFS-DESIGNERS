from __future__ import annotations

import socket
import threading
import time
from io import BytesIO
from pathlib import Path

from PySide6.QtCore import QObject, QTimer, Signal, Qt
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QPainter, QPalette, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from ems_agent.storage import (
    ApiClient,
    Counters,
    bundle_dir,
    enqueue,
    init_outbox,
    load_config,
    mark_synced,
    pending_rows,
    save_config,
)

try:
    from pynput import keyboard, mouse
except Exception:  # pragma: no cover
    mouse = None
    keyboard = None

try:
    import mss
    from PIL import Image
except Exception:  # pragma: no cover
    mss = None
    Image = None

try:
    import pygetwindow as gw
except Exception:  # pragma: no cover
    gw = None


class LiveCornerOverlay(QWidget):
    """Always-on-top corner blink (like camera REC) while Sign In / LIVE."""

    def __init__(self) -> None:
        super().__init__(None)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self._on = False
        self._label = QLabel("● LIVE", self)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 6, 10, 6)
        lay.addWidget(self._label)
        self.resize(100, 36)
        self._place()
        self.hide()

    def _place(self) -> None:
        screen = QApplication.primaryScreen()
        if not screen:
            return
        geo = screen.availableGeometry()
        self.move(geo.right() - self.width() - 16, geo.top() + 16)

    def set_live(self, active: bool) -> None:
        if active:
            self._place()
            self.show()
        else:
            self.hide()

    def tick_blink(self) -> None:
        if not self.isVisible():
            return
        self._on = not self._on
        if self._on:
            self._label.setStyleSheet(
                "color:#fff;background:#E11D1D;border-radius:8px;padding:4px 10px;"
                "border:1px solid #FF5555;"
            )
        else:
            self._label.setStyleSheet(
                "color:#fff;background:#7A0F0F;border-radius:8px;padding:4px 10px;"
                "border:1px solid #AA3333;"
            )


class CaptureService(QObject):
    status_changed = Signal(str)
    sync_changed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.cfg = load_config()
        self.counters = Counters()
        self.state = "offline"  # offline | working | break | idle
        self.session_id: str | None = None
        self._stop = threading.Event()
        self._listeners: list = []
        init_outbox()

    def start_hooks(self) -> None:
        if not mouse or not keyboard:
            self.sync_changed.emit("Hooks unavailable")
            return

        def on_click(x, y, button, pressed):
            if pressed and self.state in ("working", "idle"):
                self.counters.add_click()

        def on_press(key):
            if self.state in ("working", "idle"):
                self.counters.add_key()

        ml = mouse.Listener(on_click=on_click)
        kl = keyboard.Listener(on_press=on_press)
        ml.daemon = True
        kl.daemon = True
        ml.start()
        kl.start()
        self._listeners = [ml, kl]

    def active_window(self) -> str:
        if not gw:
            return ""
        try:
            w = gw.getActiveWindow()
            return (w.title if w else "")[:500]
        except Exception:
            return ""

    def take_screenshot_jpeg(self) -> bytes | None:
        if not mss or not Image:
            return None
        with mss.mss() as sct:
            # monitors[0] = combined virtual screen covering ALL monitors.
            # monitors[1] = primary only, monitors[2] = secondary, etc.
            # Using [0] ensures dual-monitor setups are fully captured.
            mon = sct.monitors[0]
            shot = sct.grab(mon)
            img = Image.frombytes("RGB", shot.size, shot.rgb)
            # Discard near-blank captures (sleep wake / lid closed / black screen)
            sample = img.resize((64, 36))
            extrema = sample.convert("L").getextrema()
            # getextrema → (min, max); flat image ≈ blank
            if extrema[1] - extrema[0] < 12:
                return None
            hist = sample.convert("L").histogram()
            peak = max(hist) if hist else 0
            if peak > 0.92 * sum(hist):
                return None
            # Keep width ≤ 1920 so dual-monitor shots (e.g. 3840×1080) stay
            # readable without ballooning file size.
            img.thumbnail((1920, 1080))
            # Optional privacy blur (config.json: screenshot_blur true)
            if bool(self.cfg.get("screenshot_blur", False)):
                try:
                    from PIL import ImageFilter

                    radius = float(self.cfg.get("screenshot_blur_radius", 2) or 2)
                    img = img.filter(ImageFilter.GaussianBlur(radius=max(0.5, min(radius, 8))))
                except Exception:
                    pass
            buf = BytesIO()
            img.save(buf, format="JPEG", quality=70, optimize=True)
            return buf.getvalue()

    def set_state(self, state: str) -> None:
        self.state = state
        self.status_changed.emit(state)

    def punch(self, punch_type: str) -> tuple[bool, str]:
        import uuid
        from datetime import datetime, timezone

        # Apply local UI state only after server OK (or queued offline)
        payload = {
            "id": str(uuid.uuid4()),
            "type": punch_type,
            "client_sent_at": datetime.now(timezone.utc).isoformat(),
            "session_id": self.session_id if punch_type != "sign_in" else None,
        }
        if punch_type == "sign_in":
            payload["session_id"] = str(uuid.uuid4())

        token = self.cfg.get("device_token") or ""
        if not token:
            return False, "This PC is not enrolled."

        client = ApiClient(self.cfg["api_base"], token)
        try:
            ok, err = client.punch(payload)
            if ok:
                if punch_type == "sign_in":
                    self.session_id = payload["session_id"]
                    self.set_state("working")
                elif punch_type == "break_in":
                    self.set_state("break")
                elif punch_type == "break_out":
                    self.set_state("working")
                elif punch_type == "sign_out":
                    self.set_state("offline")
                    self.session_id = None
                self.sync_changed.emit("Online")
                return True, ""
            # Server rejected — do not change local state
            return False, err or "Action was rejected by the server."
        except Exception:
            # Offline: queue and apply locally so employee can continue
            enqueue("punch", payload)
            if punch_type == "sign_in":
                self.session_id = payload["session_id"]
                self.set_state("working")
            elif punch_type == "break_in":
                self.set_state("break")
            elif punch_type == "break_out":
                self.set_state("working")
            elif punch_type == "sign_out":
                self.set_state("offline")
                self.session_id = None
            self.sync_changed.emit("Offline — punch queued")
            return True, ""

    def flush_sync(self) -> None:
        token = self.cfg.get("device_token") or ""
        if not token:
            self.sync_changed.emit("Not enrolled")
            return
        client = ApiClient(self.cfg["api_base"], token)
        online = True
        for oid, kind, payload_s in pending_rows():
            import json

            payload = json.loads(payload_s)
            try:
                ok = False
                if kind == "punch":
                    ok, _ = client.punch(payload)
                elif kind == "activity":
                    ok = client.activity(payload)
                elif kind == "screenshot":
                    path = payload.get("path")
                    if path and Path(path).is_file():
                        ok = client.screenshot(open(path, "rb").read())
                if ok:
                    mark_synced(oid)
                else:
                    online = False
                    break
            except Exception:
                online = False
                break
        self.sync_changed.emit("Online" if online else "Offline — will retry")


APP_DISPLAY_NAME = "CFS Designers Agent"


class AppDialog(QDialog):
    """Black / gold / white dialog. Red = quit or stop. Green = go ahead."""

    def __init__(
        self,
        parent: QWidget | None,
        heading: str,
        body: str = "",
        *,
        confirm: str = "OK",
        cancel: str | None = "Cancel",
        kind: str = "neutral",
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(APP_DISPLAY_NAME)
        self.setWindowIcon(_app_icon())
        self.setModal(True)
        self.setFixedWidth(380)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, False)
        self.setStyleSheet(
            """
            QDialog { background: #0A0A0A; }
            QLabel#dlgHead { color: #FFFFFF; font-size: 15px; font-weight: 600; }
            QLabel#dlgBody { color: #B3B3B3; font-size: 13px; }
            QPushButton {
                min-width: 96px; padding: 8px 18px; border-radius: 6px; font-weight: 600;
            }
            QPushButton#dlgCancel {
                background: #141414; color: #F5F5F5; border: 1px solid #3A3A3A;
            }
            QPushButton#dlgCancel:hover { border-color: #C9A227; color: #FFFFFF; }
            QPushButton#dlgNeutral { background: #C9A227; color: #0A0A0A; border: none; }
            QPushButton#dlgNeutral:hover { background: #E0B93A; }
            QPushButton#dlgDanger { background: #B42318; color: #FFFFFF; border: none; }
            QPushButton#dlgDanger:hover { background: #D92D20; }
            QPushButton#dlgSuccess { background: #1B7A3A; color: #FFFFFF; border: none; }
            QPushButton#dlgSuccess:hover { background: #21964A; }
            """
        )
        lay = QVBoxLayout(self)
        lay.setContentsMargins(22, 20, 22, 18)
        lay.setSpacing(12)
        head = QLabel(heading)
        head.setObjectName("dlgHead")
        head.setWordWrap(True)
        lay.addWidget(head)
        if body:
            note = QLabel(body)
            note.setObjectName("dlgBody")
            note.setWordWrap(True)
            lay.addWidget(note)
        row = QHBoxLayout()
        row.setSpacing(8)
        row.addStretch(1)
        cancel_btn = None
        if cancel:
            cancel_btn = QPushButton(cancel)
            cancel_btn.setObjectName("dlgCancel")
            cancel_btn.setCursor(Qt.PointingHandCursor)
            cancel_btn.clicked.connect(self.reject)
            row.addWidget(cancel_btn)
        ok = QPushButton(confirm)
        ok.setObjectName({"danger": "dlgDanger", "success": "dlgSuccess"}.get(kind, "dlgNeutral"))
        ok.setCursor(Qt.PointingHandCursor)
        ok.clicked.connect(self.accept)
        if kind == "danger" and cancel_btn is not None:
            cancel_btn.setDefault(True)
            ok.setDefault(False)
        else:
            ok.setDefault(True)
        row.addWidget(ok)
        lay.addLayout(row)


def _ask(
    parent: QWidget | None,
    heading: str,
    body: str = "",
    *,
    confirm: str = "OK",
    cancel: str = "Cancel",
    kind: str = "neutral",
) -> bool:
    return (
        AppDialog(parent, heading, body, confirm=confirm, cancel=cancel, kind=kind).exec()
        == QDialog.DialogCode.Accepted
    )


def _notice(
    parent: QWidget | None,
    heading: str,
    body: str = "",
    *,
    kind: str = "neutral",
) -> None:
    AppDialog(parent, heading, body, confirm="OK", cancel=None, kind=kind).exec()


def _assets_dir() -> Path:
    return bundle_dir() / "assets"


def _app_icon() -> QIcon:
    assets = _assets_dir()
    for name in ("cfs-agent.ico", "cfs-logo.png"):
        path = assets / name
        if path.is_file():
            return QIcon(str(path))
    size = 64
    pm = QPixmap(size, size)
    pm.fill(QColor("#0A0A0A"))
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QColor("#C9A227"))
    painter.setPen(Qt.NoPen)
    painter.drawRoundedRect(4, 4, size - 8, size - 8, 12, 12)
    painter.setPen(QColor("#0A0A0A"))
    font = QFont("Georgia", 16, QFont.Bold)
    painter.setFont(font)
    painter.drawText(pm.rect(), Qt.AlignCenter, "CFS")
    painter.end()
    return QIcon(pm)


class MainWindow(QWidget):
    enroll_finished = Signal(object, str)  # data dict or None, error message

    def __init__(self) -> None:
        super().__init__()
        self.svc = CaptureService()
        self.setWindowTitle(APP_DISPLAY_NAME)
        self.setWindowIcon(_app_icon())
        self.setMinimumSize(420, 470)
        self.setMaximumWidth(460)
        # Keep Close + Minimize. Do not use MSWindowsFixedSizeDialogHint —
        # on Windows that can grey out / disable the title-bar X.
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowSystemMenuHint
            | Qt.WindowType.WindowMinimizeButtonHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        self._apply_theme()
        self._tray: QSystemTrayIcon | None = None
        self._force_quit = False
        self._enroll_busy = False
        self.enroll_finished.connect(self._on_enroll_finished)

        self.live = QLabel("OFF")
        self.live.setAlignment(Qt.AlignCenter)
        self.live.setFixedSize(68, 68)
        self.live.setStyleSheet(self._badge_style(False))

        self.info = QLabel("Sign in to start tracking")
        self.info.setObjectName("statusTitle")
        self.info.setWordWrap(True)
        self.sync = QLabel("Connection: —")
        self.sync.setObjectName("statusMeta")
        self.sync.setWordWrap(True)

        self.enroll = QLineEdit()
        self.enroll.setPlaceholderText("Enroll code from your manager")
        self.btn_enroll = QPushButton("Enroll this PC")
        self.btn_enroll.setObjectName("primary")
        self.btn_enroll.setCursor(Qt.PointingHandCursor)
        self.btn_enroll.clicked.connect(self.do_enroll)
        self.enroll_status = QLabel("")
        self.enroll_status.setObjectName("enrollHint")
        self.enroll_status.setWordWrap(True)

        self.btn_in = QPushButton("Sign In")
        self.btn_in.setObjectName("success")
        self.btn_break_in = QPushButton("Break In")
        self.btn_break_in.setObjectName("secondary")
        self.btn_break_out = QPushButton("Break Out")
        self.btn_break_out.setObjectName("secondary")
        self.btn_out = QPushButton("Sign Out")
        self.btn_out.setObjectName("danger")
        for b, t in (
            (self.btn_in, "sign_in"),
            (self.btn_break_in, "break_in"),
            (self.btn_break_out, "break_out"),
            (self.btn_out, "sign_out"),
        ):
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda checked=False, pt=t: self.on_punch(pt))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(12)

        header = QWidget()
        header_row = QHBoxLayout(header)
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(12)
        logo = QLabel()
        logo.setFixedSize(42, 42)
        logo.setScaledContents(True)
        logo_path = _assets_dir() / "cfs-logo.png"
        if logo_path.is_file():
            logo.setPixmap(QPixmap(str(logo_path)))
        titles = QVBoxLayout()
        titles.setSpacing(1)
        titles.setContentsMargins(0, 2, 0, 0)
        brand = QLabel("CFS Designers")
        brand.setObjectName("brand")
        sub = QLabel("Time tracking")
        sub.setObjectName("subtitle")
        titles.addWidget(brand)
        titles.addWidget(sub)
        header_row.addWidget(logo)
        header_row.addLayout(titles, 1)
        layout.addWidget(header)

        rule = QWidget()
        rule.setFixedHeight(1)
        rule.setObjectName("goldRule")
        layout.addWidget(rule)

        status = QWidget()
        status.setObjectName("statusCard")
        top = QHBoxLayout(status)
        top.setContentsMargins(14, 14, 16, 14)
        top.setSpacing(14)
        top.addWidget(self.live, 0, Qt.AlignmentFlag.AlignTop)
        text_col = QVBoxLayout()
        text_col.setSpacing(4)
        text_col.setContentsMargins(0, 6, 0, 0)
        text_col.addWidget(self.info)
        text_col.addWidget(self.sync)
        top.addLayout(text_col, 1)
        layout.addWidget(status)

        layout.addWidget(self.enroll_status)
        layout.addWidget(self.enroll)
        layout.addWidget(self.btn_enroll)
        layout.addWidget(self.btn_in)
        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(self.btn_break_in)
        row.addWidget(self.btn_break_out)
        layout.addLayout(row)
        layout.addWidget(self.btn_out)

        self.svc.status_changed.connect(self.on_status)
        self.svc.sync_changed.connect(self._on_sync_text)
        self.svc.start_hooks()

        self.blink_on = False
        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self._blink)
        self.blink_timer.start(500)

        self._corner = LiveCornerOverlay()

        self.activity_timer = QTimer(self)
        self.activity_timer.timeout.connect(self._tick_activity)
        self.activity_timer.start(int(self.svc.cfg.get("activity_interval_seconds", 15)) * 1000)

        self.shot_timer = QTimer(self)
        self.shot_timer.timeout.connect(self._tick_screenshot)
        # First capture soon after Sign In; recurring interval from config (default 5 min)
        self.shot_timer.start(int(self.svc.cfg.get("screenshot_interval_seconds", 300)) * 1000)

        self._auto_out_busy = False
        self._skip_shots_until = 0.0
        self._last_activity_tick = time.time()
        self._server_signed_in = False
        self._update_buttons()
        self._refresh_enroll_ui()
        if self.svc.cfg.get("device_token"):
            self._on_sync_text("Ready")
            QTimer.singleShot(800, self._sync_server_session)

        self.session_timer = QTimer(self)
        self.session_timer.timeout.connect(self._sync_server_session)
        self.session_timer.start(45_000)

        self._setup_tray()

    def _setup_tray(self) -> None:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        tray = QSystemTrayIcon(self)
        tray.setIcon(_app_icon())
        tray.setToolTip(APP_DISPLAY_NAME)
        menu = QMenu()
        act_open = QAction("Open", self)
        act_open.triggered.connect(self._show_from_tray)
        act_quit = QAction("Quit", self)
        act_quit.triggered.connect(self._confirm_quit)
        menu.addAction(act_open)
        menu.addSeparator()
        menu.addAction(act_quit)
        tray.setContextMenu(menu)
        tray.activated.connect(self._on_tray_activated)
        tray.show()
        self._tray = tray

    def _show_from_tray(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self._show_from_tray()

    def _confirm_quit(self) -> None:
        if _ask(self, "Quit CFS Designers Agent?", confirm="Quit", kind="danger"):
            self._force_quit = True
            QApplication.instance().quit()

    def closeEvent(self, event) -> None:  # noqa: N802 — Qt API
        if self._force_quit:
            event.accept()
            return
        event.ignore()
        self._confirm_quit()

    def _sync_server_session(self) -> None:
        token = self.svc.cfg.get("device_token") or ""
        if not token:
            self._server_signed_in = False
            self._update_buttons()
            return
        try:
            st = ApiClient(self.svc.cfg["api_base"], token).session_status()
            self._server_signed_in = bool(st.get("signed_in"))
            if self._server_signed_in and self.svc.state == "offline":
                sid = st.get("session_id")
                if sid:
                    self.svc.session_id = sid
                self.info.setText(
                    "An open session is still on the server.\n"
                    "Tap End Session, then Sign In to continue."
                )
                self.enroll_status.setStyleSheet("color: #F59E0B; font-weight: 600;")
        except Exception:
            pass
        self._update_buttons()

    def nativeEvent(self, eventType, message):  # noqa: N802 — Qt API
        from ems_agent.power_watch import handle_windows_native_event

        handled = handle_windows_native_event(
            eventType,
            message,
            on_sleep=self._on_power_sleep,
            on_resume=self._on_power_resume,
        )
        if handled is not None:
            return handled
        return super().nativeEvent(eventType, message)

    def _on_power_sleep(self) -> None:
        if not self.svc.cfg.get("auto_sign_out_on_sleep", True):
            return
        self._auto_sign_out("Session ended")

    def _on_power_resume(self) -> None:
        # After wake: never keep counting; require fresh Sign In
        self._skip_shots_until = time.time() + 90
        if self.svc.state != "offline":
            self._auto_sign_out("Session ended")

    def _auto_sign_out(self, reason: str) -> None:
        if self._auto_out_busy:
            return
        if self.svc.state == "offline":
            return
        if not self.svc.cfg.get("device_token"):
            return
        self._auto_out_busy = True
        try:
            ok, err = self.svc.punch("sign_out")
            if ok:
                self.info.setText(f"{reason}. Tap Sign In to resume.")
                self.svc.sync_changed.emit("Ready")
                self._server_signed_in = False
            elif err and "already signed out" in err.lower():
                self.svc.set_state("offline")
                self.svc.session_id = None
                self._server_signed_in = False
                self.info.setText("Signed out.")
            else:
                self.svc.set_state("offline")
                self.svc.session_id = None
                self.info.setText(
                    f"{reason}. Tap End Session when connected."
                )
        finally:
            self._auto_out_busy = False
            self._update_buttons()

    def _on_sync_text(self, s: str) -> None:
        # Connected ≠ tracking. Tracking = Sign In (LIVE).
        st = self.svc.state
        raw = (s or "").strip()
        low = raw.lower()
        if "queue" in low or "offline" in low:
            label = "Connection: Offline — will retry"
        elif st == "working":
            label = "Connection: Online · tracking"
        elif st == "break":
            label = "Connection: Online · on break"
        elif st == "idle":
            label = "Connection: Online · idle"
        elif "enroll" in low:
            label = f"Connection: {raw}"
        elif raw in ("Online", "Ready", "Online — tracking"):
            label = "Connection: Ready (signed out)"
        else:
            label = f"Connection: {raw}" if raw else "Connection: —"
        self.sync.setText(label)

    def _apply_theme(self) -> None:
        self.setStyleSheet(
            """
            QWidget { background: #0A0A0A; color: #F5F5F5; font-size: 14px; }
            QLabel#brand { color: #C9A227; font-size: 18px; font-weight: 700; }
            QLabel#subtitle { color: #8A8A8A; font-size: 12px; }
            QWidget#goldRule { background: #C9A227; }
            QWidget#statusCard {
                background: #141414;
                border: 1px solid #2C2C2C;
                border-radius: 10px;
            }
            QLabel#statusTitle { color: #FFFFFF; font-size: 15px; font-weight: 600; }
            QLabel#statusMeta { color: #8A8A8A; font-size: 12px; }
            QLabel#enrollHint { color: #C9A227; font-size: 13px; }
            QPushButton {
                border: none; padding: 11px 14px;
                border-radius: 7px; font-weight: 600;
            }
            QPushButton#primary { background: #C9A227; color: #0A0A0A; }
            QPushButton#primary:hover { background: #E0B93A; }
            QPushButton#success { background: #1B7A3A; color: #FFFFFF; }
            QPushButton#success:hover { background: #21964A; }
            QPushButton#danger { background: #B42318; color: #FFFFFF; }
            QPushButton#danger:hover { background: #D92D20; }
            QPushButton#secondary {
                background: #161616; color: #F0E6C8;
                border: 1px solid #6B5A22;
            }
            QPushButton#secondary:hover { background: #1F1A0C; border-color: #C9A227; }
            QPushButton#ghost {
                background: transparent; color: #D4D4D4;
                border: 1px solid #3A3A3A;
            }
            QPushButton#ghost:hover { border-color: #8A8A8A; color: #FFFFFF; }
            QPushButton:disabled {
                background: #1C1C1C; color: #6A6A6A; border: 1px solid #2A2A2A;
            }
            QLineEdit {
                background: #141414; border: 1px solid #3A3A3A; padding: 10px 12px;
                border-radius: 7px; color: #FFFFFF;
            }
            QLineEdit:focus { border: 1px solid #C9A227; }
            """
        )

    def _badge_style(self, live: bool, break_: bool = False, dim: bool = False) -> str:
        if break_:
            return "background:#F59E0B;color:#0A0A0A;border-radius:36px;font-weight:700;"
        if live:
            bg = "#AA1010" if dim else "#FF2020"
            return f"background:{bg};color:#fff;border-radius:36px;font-weight:700;border:2px solid #FF4444;"
        return "background:#333333;color:#A3A3A3;border-radius:36px;font-weight:700;"

    def _blink(self) -> None:
        st = self.svc.state
        if st == "working":
            self.blink_on = not self.blink_on
            # Keep text stable; only swap brightness (avoids Qt painter spam)
            if self.live.text() != "LIVE":
                self.live.setText("LIVE")
            style = self._badge_style(True, dim=not self.blink_on)
            if getattr(self, "_live_style", "") != style:
                self._live_style = style
                self.live.setStyleSheet(style)
            if getattr(self, "_corner", None):
                self._corner.set_live(True)
                self._corner.tick_blink()
        elif st == "break":
            if self.live.text() != "BREAK":
                self.live.setText("BREAK")
            style = self._badge_style(False, True)
            if getattr(self, "_live_style", "") != style:
                self._live_style = style
                self.live.setStyleSheet(style)
            if getattr(self, "_corner", None):
                self._corner.set_live(False)
        elif st == "idle":
            if self.live.text() != "IDLE":
                self.live.setText("IDLE")
            style = self._badge_style(False, True)
            if getattr(self, "_live_style", "") != style:
                self._live_style = style
                self.live.setStyleSheet(style)
            if getattr(self, "_corner", None):
                self._corner.set_live(True)
                self._corner.tick_blink()
        else:
            if self.live.text() != "OFF":
                self.live.setText("OFF")
            style = self._badge_style(False)
            if getattr(self, "_live_style", "") != style:
                self._live_style = style
                self.live.setStyleSheet(style)
            if getattr(self, "_corner", None):
                self._corner.set_live(False)

    def _refresh_enroll_ui(self) -> None:
        token = self.svc.cfg.get("device_token")
        name = (self.svc.cfg.get("employee_name") or "").strip() or "employee"
        code = (self.svc.cfg.get("employee_code") or "").strip()
        host = socket.gethostname()
        if token:
            self.enroll.hide()
            self.btn_enroll.hide()
            self.enroll_status.setStyleSheet("color: #C9A227; font-weight: 600;")
            who = f"{name}" + (f" (#{code})" if code else "")
            # Keep window title = app name so Windows does not show "Name - CFS Designers Agent"
            self.enroll_status.setText(f"Enrolled as {who}\nThis PC: {host}")
            self.enroll_status.show()
            self.setWindowTitle(APP_DISPLAY_NAME)
        else:
            self.enroll.show()
            self.btn_enroll.show()
            self.btn_enroll.setText("Enroll this PC")
            self.btn_enroll.setEnabled(True)
            self.enroll_status.setText("Not enrolled. Paste the manager code, then Enroll this PC.")
            self.enroll_status.setStyleSheet("color: #A3A3A3;")
            self.setWindowTitle(APP_DISPLAY_NAME)

    def on_status(self, state: str) -> None:
        names = {
            "working": "LIVE — monitoring on. Work normally.",
            "break": "On break — screenshots paused.",
            "idle": "Idle — no mouse/keyboard recently.",
            "offline": "Signed out — tracking stopped on this PC.",
        }
        self.info.setText(names.get(state, state))
        self._update_buttons()
        # Refresh connection line so Ready vs tracking stays accurate
        cur = self.sync.text().replace("Connection: ", "")
        if "Offline" in cur or "queue" in cur.lower():
            self._on_sync_text(cur)
        else:
            self._on_sync_text("Online" if state != "offline" else "Ready")

    def _update_buttons(self) -> None:
        st = self.svc.state
        stuck = self._server_signed_in and st == "offline"
        self.btn_in.setEnabled(st == "offline" and not stuck)
        self.btn_break_in.setEnabled(st == "working" or st == "idle")
        self.btn_break_out.setEnabled(st == "break")
        self.btn_out.setEnabled(st != "offline" or stuck)
        if stuck:
            self.btn_out.setText("End Session")
        else:
            self.btn_out.setText("Sign Out")

    def on_punch(self, punch_type: str) -> None:
        if not self.svc.cfg.get("device_token"):
            _notice(self, "This PC is not enrolled.", "Ask your manager for an enroll code.")
            return
        ok, err = self.svc.punch(punch_type)
        if not ok and punch_type == "sign_in" and err and "already signed in" in err.lower():
            if _ask(
                self,
                "End the open session and sign in?",
                confirm="Sign In",
                kind="success",
            ):
                out_ok, out_err = self.svc.punch("sign_out")
                if out_ok:
                    self._server_signed_in = False
                    ok, err = self.svc.punch("sign_in")
                else:
                    _notice(self, "Could not end session.", out_err or "Try End Session, then Sign In.")
                    self._sync_server_session()
                    return
        if not ok:
            _notice(self, "Could not save.", err or "Check your connection and try again.")
            return
        if punch_type == "sign_out":
            self._server_signed_in = False
        elif punch_type == "sign_in":
            self._server_signed_in = True
        self._sync_server_session()
        if punch_type == "sign_in":
            QTimer.singleShot(2500, self._tick_screenshot)

    def do_enroll(self) -> None:
        if self._enroll_busy:
            return
        if self.svc.cfg.get("device_token"):
            name = self.svc.cfg.get("employee_name") or "an employee"
            _notice(self, "This PC is already enrolled.", f"Linked to {name}.")
            self._refresh_enroll_ui()
            return
        code = self.enroll.text().strip()
        if not code:
            self.enroll_status.setText("Enter the enroll code from your manager.")
            self.enroll_status.setStyleSheet("color: #E8A0A8; font-weight: 600;")
            _notice(self, "Enter the enroll code from your manager.")
            return

        self._enroll_busy = True
        self.btn_enroll.setEnabled(False)
        self.btn_enroll.setText("Connecting...")
        self.enroll.setEnabled(False)
        self.enroll_status.setText("Checking enroll code with server...")
        self.enroll_status.setStyleSheet("color: #C9A227; font-weight: 600;")
        self.sync.setText("Connection: Checking...")

        api_base = str(self.svc.cfg.get("api_base") or "").rstrip("/")
        hostname = socket.gethostname()

        def work() -> None:
            try:
                client = ApiClient(api_base, "")
                data = client.enroll(code, hostname)
                self.enroll_finished.emit(data, "")
            except Exception as e:
                msg = str(e).strip() or "Enroll failed. Try again."
                if "For more information check" in msg or "httpx" in msg.lower() or "Bad Request" in msg:
                    msg = (
                        "Wrong enroll code (invalid or already used).\n\n"
                        "Ask your manager for a new code."
                    )
                self.enroll_finished.emit(None, msg)

        threading.Thread(target=work, daemon=True).start()

    def _on_enroll_finished(self, data: object, err: str) -> None:
        self._enroll_busy = False
        self.enroll.setEnabled(True)
        self.btn_enroll.setEnabled(True)
        self.btn_enroll.setText("Enroll this PC")

        if data and isinstance(data, dict):
            self.svc.cfg["device_token"] = data["device_token"]
            self.svc.cfg["employee_name"] = data.get("employee_name", "")
            self.svc.cfg["employee_code"] = data.get("employee_code", "")
            save_config(self.svc.cfg)
            self.sync.setText(f"Sync: Enrolled as {data.get('employee_name')}")
            self.enroll.clear()
            self._refresh_enroll_ui()
            _notice(
                self,
                "PC enrolled.",
                f"Linked to {data.get('employee_name')} ({data.get('employee_code')}). You can sign in now.",
                kind="success",
            )
            return

        msg = err or "Enroll failed. Try again."
        self.enroll_status.setText(msg)
        self.enroll_status.setStyleSheet("color: #E8A0A8; font-weight: 600;")
        low = msg.lower()
        if "wrong enroll" in low or "invalid" in low or "already used" in low:
            self.sync.setText("Connection: Wrong code")
            _notice(self, "Wrong enroll code.", msg, kind="danger")
        elif "timed out" in low or "cannot reach" in low or "could not contact" in low:
            self.sync.setText("Connection: Offline")
            _notice(self, "Cannot reach server.", msg, kind="danger")
        else:
            self.sync.setText("Connection: Enroll failed")
            _notice(self, "Enroll failed.", msg, kind="danger")

    def _tick_activity(self) -> None:
        if self.svc.state not in ("working", "break", "idle"):
            return
        if not self._server_signed_in:
            return
        # Reliable sleep detect: Qt timers pause during suspend — big gap on wake
        now = time.time()
        gap = now - self._last_activity_tick
        self._last_activity_tick = now
        sleep_gap = float(self.svc.cfg.get("sleep_gap_seconds", 120))
        if gap >= sleep_gap and self.svc.state != "offline":
            self._auto_sign_out("Session ended")
            return

        clicks, keys, last_input = self.svc.counters.drain()
        idle_for = time.time() - last_input
        idle_limit = float(self.svc.cfg.get("idle_seconds", 180))
        auto_out = float(self.svc.cfg.get("auto_sign_out_idle_seconds", 1800))
        status = self.svc.state
        if self.svc.state in ("working", "idle"):
            if auto_out > 0 and idle_for >= auto_out:
                self._auto_sign_out("Session ended")
                return
            if idle_for >= idle_limit:
                status = "idle"
                self.svc.set_state("idle")
            else:
                status = "working"
                if self.svc.state == "idle":
                    self.svc.set_state("working")
        if self.svc.state == "break":
            status = "break"
            # Break is intentional — do not auto Sign Out on idle alone.
            # Sleep / shutdown still auto Sign Out via power hooks.
        payload = {
            "mouse_clicks": clicks,
            "key_presses": keys,
            "window_title": self.svc.active_window() if status != "break" else "",
            "idle_seconds": int(min(idle_for, self.svc.cfg.get("activity_interval_seconds", 15)))
            if status == "idle"
            else 0,
            "status": status,
        }
        # try live post; also keep resilience via direct API
        token = self.svc.cfg.get("device_token") or ""
        if not token:
            return
        try:
            ApiClient(self.svc.cfg["api_base"], token).activity(payload)
            self.svc.sync_changed.emit("Online")
        except Exception:
            enqueue("activity", payload)
            self.svc.sync_changed.emit("Offline — queued")

    def _tick_screenshot(self) -> None:
        if self.svc.state not in ("working", "idle"):
            return
        # skip while idle (professional default)
        if self.svc.state == "idle":
            return
        if time.time() < self._skip_shots_until:
            return
        data = self.svc.take_screenshot_jpeg()
        if not data:
            return
        from pathlib import Path
        import uuid

        path = Path(__file__).resolve().parents[1] / "agent_data" / "shots"
        path.mkdir(parents=True, exist_ok=True)
        f = path / f"{uuid.uuid4()}.jpg"
        f.write_bytes(data)
        token = self.svc.cfg.get("device_token") or ""
        if not token:
            return
        try:
            ok = ApiClient(self.svc.cfg["api_base"], token).screenshot(data)
            if ok:
                self.svc.sync_changed.emit("Online")
                try:
                    f.unlink()
                except OSError:
                    pass
            else:
                enqueue("screenshot", {"path": str(f)})
        except Exception:
            enqueue("screenshot", {"path": str(f)})
            self.svc.sync_changed.emit("Offline — shot queued")


def _hide_windows_console() -> None:
    """Remove the extra black console so only the Agent UI is visible."""
    import sys

    if sys.platform != "win32":
        return
    try:
        import ctypes

        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)
        ctypes.windll.kernel32.FreeConsole()
    except Exception:
        pass


def main() -> None:
    import sys

    from PySide6.QtCore import QSharedMemory

    _hide_windows_console()
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("CFSDesigners.Agent")
    except Exception:
        pass

    lock = QSharedMemory("CFSDesigners.Agent.SingleInstance")
    if not lock.create(1):
        sys.exit(0)

    app = QApplication(sys.argv)
    app._instance_lock = lock  # noqa: SLF001 — keep mutex alive
    app.setApplicationName(APP_DISPLAY_NAME)
    app.setApplicationDisplayName(APP_DISPLAY_NAME)
    app.setWindowIcon(_app_icon())
    app.setQuitOnLastWindowClosed(False)
    app.setFont(QFont("Segoe UI", 10))
    w = MainWindow()

    def _quit_sign_out() -> None:
        if w.svc.state != "offline" and w.svc.cfg.get("auto_sign_out_on_sleep", True):
            w._auto_sign_out("Session ended")

    app.aboutToQuit.connect(_quit_sign_out)
    try:
        app.applicationStateChanged.connect(
            lambda state: w._on_power_sleep()
            if state == Qt.ApplicationState.ApplicationSuspended
            else None
        )
    except Exception:
        pass
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
