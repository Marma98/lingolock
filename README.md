# LingoLock

> Block social media. Earn access by completing a language challenge.

LingoLock is an Android app that intercepts the launch of social media apps (Instagram, TikTok, etc.) and requires the user to translate a set of vocabulary words before being granted access. The harder you try to procrastinate, the harder the challenge gets.

---

## How it works

1. You open Instagram (or another blocked app).
2. LingoLock intercepts the launch instantly via an Android Accessibility Service.
3. A challenge screen appears: translate N words from Italian ↔ English within a time limit.
4. **Pass** → the app opens.
5. **Fail / timeout** → locked out, attempt recorded.
6. Each failed attempt within a session increases the word count and shrinks the time limit (adaptive difficulty).

Blocking is only active during user-defined **sessions** (e.g. "Work: 08:00–12:00"), so your evenings stay free.

---

## Features

- **App gatekeeper** — instant overlay via `TYPE_WINDOW_STATE_CHANGED` accessibility event
- **Flashcard-style challenges** — Italian ↔ English translation, ordered by worst success rate first
- **Custom vocabulary** — add the words you actually want to learn
- **Session scheduling** — time-based blocking windows, supports overnight sessions
- **Adaptive difficulty** — `words = min(base + N, 10)`, `time = max(base − N×5, 10s)`
- **Offline / no account** — everything stored in local SQLite

---

## Tech stack

| Layer | Technology |
|---|---|
| UI | Python + [KivyMD](https://kivymd.readthedocs.io) |
| Android bridge | [pyjnius](https://pyjnius.readthedocs.io) + Java Accessibility Service |
| Database | SQLite (via `sqlite3`, no ORM) |
| Background service | python-for-android foreground service |
| Build | [Buildozer](https://buildozer.readthedocs.io) inside Docker devcontainer |
| Tests | pytest |

---

## Project structure

```
lingolock/
├── src/
│   ├── main.py                  # App entry point, ScreenManager, IPC poll
│   ├── database/
│   │   ├── db.py                # Schema, per-thread connection
│   │   ├── queries.py           # All SQL operations
│   │   └── models.py            # Plain dataclasses
│   ├── logic/
│   │   ├── challenge_engine.py  # Difficulty, build_challenge, evaluate_answer
│   │   ├── session_manager.py   # is_blocking_active, overnight session support
│   │   └── permissions.py       # Android permission helpers (graceful desktop fallback)
│   ├── services/
│   │   ├── monitor_service.py   # p4a background service, polls UsageStatsManager
│   │   └── ipc.py               # Atomic trigger/ack file protocol
│   └── ui/
│       ├── kv/                  # KV layout files (one per screen)
│       └── screens/             # ChallengeScreen, HomeScreen, SessionsScreen, …
├── android/
│   ├── java/com/lingoblock/
│   │   ├── LingoAccessibilityService.java
│   │   └── OverlayReceiver.java
│   └── res/xml/accessibility_service_config.xml
├── tests/
├── .devcontainer/               # VS Code devcontainer (Docker)
├── buildozer.spec
└── requirements.txt
```

---

## Getting started

### Prerequisites

- [VS Code](https://code.visualstudio.com/) with the **Dev Containers** extension
- Docker Desktop

### 1. Open in devcontainer

```
File → Open Folder → lingolock
→ "Reopen in Container"
```

The container installs the Android SDK/NDK, Python, and all dependencies automatically.

### 2. Run tests (desktop)

```bash
python -m pytest tests/ -v
```

### 3. Run the UI on desktop (no Android needed)

```bash
python src/main.py
```

### 4. Build the APK

```bash
buildozer android debug
```

### 5. Deploy to a connected device

```bash
adb install bin/lingolock-0.1.0-arm64-v8a-debug.apk
adb logcat -s python   # stream logs
```

---

## Android permissions

| Permission | Why |
|---|---|
| `BIND_ACCESSIBILITY_SERVICE` | Detect app launches instantly |
| `PACKAGE_USAGE_STATS` | Background monitor fallback via UsageStatsManager |
| `SYSTEM_ALERT_WINDOW` | Draw the challenge overlay on top of other apps |
| `FOREGROUND_SERVICE` | Keep the monitor service alive |
| `RECEIVE_BOOT_COMPLETED` | Restart the service after reboot |

`PACKAGE_USAGE_STATS` and `SYSTEM_ALERT_WINDOW` require manual grant via Android Settings — the app guides you through this on first launch.

---

## License

MIT
