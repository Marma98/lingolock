"""Background service entry-point (python-for-android).

On Android this runs in a separate process as a sticky foreground service.
On desktop it runs as a simple blocking loop (for integration testing).

p4a service declaration in buildozer.spec:
    services = Monitor:services/monitor_service.py:foreground:sticky
"""

from __future__ import annotations
import time
import sys
import os

# Make src/ importable when running inside the p4a service process.
_SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from database.db import init_db
from database.queries import get_enabled_blocked_packages
from logic.session_manager import is_blocking_active
from services.ipc import write_trigger, read_ack

POLL_INTERVAL = 1.5   # seconds
COOLDOWN      = 10.0  # seconds per package

_cooldowns: dict[str, float] = {}

try:
    from jnius import autoclass  # type: ignore

    UsageStatsManager = autoclass("android.app.usage.UsageStatsManager")
    UsageEvents       = autoclass("android.app.usage.UsageEvents")
    PythonService     = autoclass("org.kivy.android.PythonService")
    Context           = autoclass("android.content.Context")
    Intent            = autoclass("android.content.Intent")
    PythonActivity    = autoclass("org.kivy.android.PythonActivity")

    _ON_ANDROID = True
except Exception:
    _ON_ANDROID = False


def _get_foreground_package_android() -> str | None:
    """Return the current foreground app package name via UsageStats."""
    try:
        service = PythonService.mService
        usm = service.getSystemService(Context.USAGE_STATS_SERVICE)
        now = int(time.time() * 1000)
        events = usm.queryEvents(now - 3000, now)
        event = UsageEvents.Event()
        last_pkg = None
        while events.hasNextEvent():
            events.getNextEvent(event)
            if event.getEventType() == UsageEvents.Event.MOVE_TO_FOREGROUND:
                last_pkg = event.getPackageName()
        return last_pkg
    except Exception:
        return None


def _launch_challenge(package_name: str):
    """Bring the LingoLock PythonActivity to foreground with the trigger package."""
    if _ON_ANDROID:
        try:
            service = PythonService.mService
            intent = Intent(service, PythonActivity._class)
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_REORDER_TO_FRONT)
            intent.putExtra("trigger_package", package_name)
            service.startActivity(intent)
        except Exception as exc:
            print(f"[monitor] launch challenge error: {exc}")
    # Always write the IPC file so the main app can react
    write_trigger(package_name)


def _is_in_cooldown(pkg: str) -> bool:
    last = _cooldowns.get(pkg, 0.0)
    return (time.time() - last) < COOLDOWN


def _set_cooldown(pkg: str):
    _cooldowns[pkg] = time.time()


def run():
    init_db()
    print("[monitor] service started")

    while True:
        try:
            if is_blocking_active():
                blocked = set(get_enabled_blocked_packages())

                if _ON_ANDROID:
                    fg = _get_foreground_package_android()
                else:
                    # Desktop stub: read from IPC for testing
                    fg = None

                if fg and fg in blocked and not _is_in_cooldown(fg):
                    print(f"[monitor] blocked app detected: {fg}")
                    _launch_challenge(fg)
                    _set_cooldown(fg)

        except Exception as exc:
            print(f"[monitor] error: {exc}")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    run()
