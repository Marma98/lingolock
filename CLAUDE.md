# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Run all tests
```bash
"/c/Users/marma/AppData/Local/Programs/Python/Python312/python.exe" -m pytest tests/ -v
```

### Run a single test file
```bash
"/c/Users/marma/AppData/Local/Programs/Python/Python312/python.exe" -m pytest tests/test_challenge_engine.py -v
```

### Run a single test by name
```bash
"/c/Users/marma/AppData/Local/Programs/Python/Python312/python.exe" -m pytest tests/ -k "test_compute_difficulty"
```

### Run the desktop UI (requires Kivy installed)
```bash
"/c/Users/marma/AppData/Local/Programs/Python/Python312/python.exe" src/main.py
```

### Build APK (inside devcontainer only)
```bash
buildozer android debug
# Install to connected device:
adb install bin/lingolock-0.1.0-arm64-v8a-debug.apk
# Stream logs:
adb logcat -s python
```

### Isolate DB for testing
```bash
LINGOLOCK_DB=/tmp/test.db python src/main.py
```

## Architecture

### Data flow
```
User opens Instagram
  → LingoAccessibilityService.java (instant, TYPE_WINDOW_STATE_CHANGED)
  → sendBroadcast("com.lingoblock.APP_BLOCKED")
     + OverlayReceiver.java relaunches PythonActivity with trigger_package extra
  [parallel]
  → monitor_service.py polls UsageStatsManager every 1.5s
  → writes ~/.lingolock/ipc/trigger.json
  → main.py Clock poll picks it up → switches ScreenManager to "challenge"
  → ChallengeScreen.on_enter() builds challenge, starts countdown
  → pass: PackageManager.getLaunchIntentForPackage() → opens target app
  → fail/timeout: lockout, records attempt, returns to home
```

### Module responsibilities

**`src/database/`** — pure SQLite, no Kivy imports.
- `db.py`: schema creation, per-thread connection via `threading.local`, `init_db()` is idempotent.
- `queries.py`: every DB operation lives here as a named function. No raw SQL outside this file.
- `models.py`: plain dataclasses — no ORM.

**`src/logic/`** — pure Python, no Kivy or Android imports.
- `session_manager.py`: `is_blocking_active()` and `get_current_session()` — compares current weekday+time against enabled sessions. Supports overnight sessions (end < start).
- `challenge_engine.py`: `compute_difficulty(session_id)` → `(word_count, time_limit)`; `build_challenge(n)` → list of `{word, direction, prompt, expected}` ordered by worst success rate first; `evaluate_answer()` uses Optimal String Alignment (handles transpositions, distance ≤ 1 accepted).
- `permissions.py`: all pyjnius calls are wrapped in try/except — falls back gracefully on desktop.

**`src/services/`**
- `monitor_service.py`: p4a background service entry point. Polls `UsageStatsManager` every 1.5s; writes `~/.lingolock/ipc/trigger.json` and fires an Android Intent on detection. 10s cooldown per package.
- `ipc.py`: atomic file writes (`os.replace`) for the trigger/ack protocol.

**`src/ui/`** — KivyMD screens + KV files.
- Each screen has a matching `.kv` file in `src/ui/kv/`. KV files are loaded by name in `main.py`.
- `ChallengeScreen` overrides `on_back_pressed()` → returns `True` to block the hardware back button.
- `SettingsScreen.debug_trigger_challenge()` simulates a block trigger on desktop without Android.

**`android/`** — Java-only, compiled by Buildozer.
- `LingoAccessibilityService.java`: listens for `TYPE_WINDOW_STATE_CHANGED`, checks package against a hardcoded set (kept in sync with DB seed), broadcasts + launches PythonActivity.
- `OverlayReceiver.java`: handles `APP_BLOCKED` broadcast and `BOOT_COMPLETED` (re-starts the Python monitor service after reboot).
- `extra_manifest_application.xml` / `extra_manifest_queries.xml`: injected into the APK manifest by Buildozer via `android.extra_manifest_*` spec keys.

### Key invariants
- All SQL queries go through `src/database/queries.py` — screens and logic never call `get_connection()` directly.
- The `logic/` layer has zero Kivy/Android imports — fully testable with plain pytest on desktop.
- `init_db()` is idempotent: safe to call on every app start and in every test fixture.
- Tests use `LINGOLOCK_DB` env var to redirect to a temp file — never touch the user's real DB.
- Difficulty is adaptive per-session-per-day: `words = min(base + increment × N, 10)`, `time = max(base − decrement × N, 10)` where N = attempts in this session today.

### Android permissions that require special UX
`PACKAGE_USAGE_STATS` and `SYSTEM_ALERT_WINDOW` cannot be granted via the normal runtime permission dialog — the user must be sent to Settings screens. `permissions.py` provides `request_usage_stats_permission()` and `request_overlay_permission()` for this; `SettingsScreen` surfaces the buttons.
