"""File-based IPC between the background monitor service and the main app.

The service writes a trigger file; the main app polls and reacts.
"""

from __future__ import annotations
import os
import json
import time

_IPC_DIR = os.path.join(os.path.expanduser("~"), ".lingolock", "ipc")
_TRIGGER_FILE = os.path.join(_IPC_DIR, "trigger.json")
_ACK_FILE     = os.path.join(_IPC_DIR, "ack.json")


def _ensure_dir():
    os.makedirs(_IPC_DIR, exist_ok=True)


# ── Service side (writer) ─────────────────────────────────────────────────────

def write_trigger(package_name: str):
    """Called by the monitor service when a blocked app comes to foreground."""
    _ensure_dir()
    payload = {
        "package":   package_name,
        "timestamp": time.time(),
    }
    tmp = _TRIGGER_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(payload, f)
    os.replace(tmp, _TRIGGER_FILE)


def clear_trigger():
    try:
        os.remove(_TRIGGER_FILE)
    except FileNotFoundError:
        pass


# ── Main-app side (reader) ────────────────────────────────────────────────────

def read_trigger() -> dict | None:
    """Return trigger payload if present, else None."""
    try:
        with open(_TRIGGER_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def ack_trigger():
    """Acknowledge that the main app has handled the trigger."""
    _ensure_dir()
    payload = {"ack_time": time.time()}
    with open(_ACK_FILE, "w") as f:
        json.dump(payload, f)
    clear_trigger()


def read_ack() -> dict | None:
    try:
        with open(_ACK_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None
