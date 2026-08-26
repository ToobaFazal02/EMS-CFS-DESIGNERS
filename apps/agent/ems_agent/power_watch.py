"""Windows sleep / shutdown detection → auto Sign Out."""

from __future__ import annotations

import sys
from collections.abc import Callable

# Windows message constants
WM_POWERBROADCAST = 0x0218
WM_QUERYENDSESSION = 0x0011
WM_ENDSESSION = 0x0016
PBT_APMSUSPEND = 0x0004
PBT_APMRESUMEAUTOMATIC = 0x0012
PBT_APMRESUMESUSPEND = 0x0007
PBT_APMRESUMECRITICAL = 0x0006


def handle_windows_native_event(
    event_type,
    message,
    on_sleep: Callable[[], None],
    on_resume: Callable[[], None],
) -> tuple[bool, int] | None:
    """
    Process WM_POWERBROADCAST / session end.
    Returns (False, 0) if handled path should fall through to Qt default,
    or None if not a Windows power message (caller should call super).
    """
    if sys.platform != "win32":
        return None
    try:
        et = event_type.data().decode("utf-8", errors="ignore") if hasattr(event_type, "data") else str(event_type)
    except Exception:
        et = str(event_type)
    if "windows_generic_MSG" not in et and et not in ("windows_generic_MSG",):
        # PySide6 may pass QByteArray
        try:
            raw = bytes(event_type).decode("latin1", errors="ignore")
            if "windows_generic_MSG" not in raw:
                return None
        except Exception:
            return None

    try:
        import ctypes
        from ctypes import wintypes

        msg = wintypes.MSG.from_address(int(message))
    except Exception:
        return None

    if msg.message == WM_POWERBROADCAST:
        if msg.wParam == PBT_APMSUSPEND:
            on_sleep()
        elif msg.wParam in (PBT_APMRESUMEAUTOMATIC, PBT_APMRESUMESUSPEND, PBT_APMRESUMECRITICAL):
            on_resume()
        return False, 0

    if msg.message in (WM_QUERYENDSESSION, WM_ENDSESSION):
        # Shutting down / logging off — close session before OS kills us
        on_sleep()
        return False, 0

    return None
