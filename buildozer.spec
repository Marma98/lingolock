[app]
title = LingoLock
package.name = lingolock
package.domain = com.lingolock

source.dir = src
source.include_exts = py,png,jpg,kv,atlas,ttf,db

version = 0.1.0

requirements = python3,kivy==2.3.0,kivymd==1.2.0,pyjnius,sqlite3

# p4a background service: name:entrypoint:mode:restart_on_destroy
services = Monitor:services/monitor_service.py:foreground:sticky

# ── Android config ────────────────────────────────────────────────────────────
android.permissions =
    android.permission.PACKAGE_USAGE_STATS,
    android.permission.BIND_ACCESSIBILITY_SERVICE,
    android.permission.FOREGROUND_SERVICE,
    android.permission.FOREGROUND_SERVICE_SPECIAL_USE,
    android.permission.QUERY_ALL_PACKAGES,
    android.permission.SYSTEM_ALERT_WINDOW,
    android.permission.RECEIVE_BOOT_COMPLETED,
    android.permission.INTERNET

android.api = 34
android.minapi = 26
android.ndk = 25b
android.sdk = 34
android.arch = arm64-v8a
android.ndk_api = 26

# Inject extra Java sources, resources and manifest snippets
android.add_src = android/java
android.add_res = android/res
android.extra_manifest_application_arguments = android/extra_manifest_application.xml
android.extra_manifest_arguments = android/extra_manifest_queries.xml

android.logcat_filters = *:S python:D

# ── Buildozer options ─────────────────────────────────────────────────────────
[buildozer]
log_level = 2
warn_on_root = 1

android.accept_sdk_license = True
