"""Runtime permission requests for Android via pyjnius.

On non-Android platforms these functions are no-ops so the app can be
tested on desktop without crashing.
"""

from __future__ import annotations

try:
    from jnius import autoclass  # type: ignore

    PythonActivity = autoclass("org.kivy.android.PythonActivity")
    Intent         = autoclass("android.content.Intent")
    Settings       = autoclass("android.provider.Settings")
    Uri            = autoclass("android.net.Uri")
    Build          = autoclass("android.os.Build")

    _ON_ANDROID = True
except Exception:
    _ON_ANDROID = False


def is_android() -> bool:
    return _ON_ANDROID


def request_usage_stats_permission():
    """Open the Usage Access settings screen."""
    if not _ON_ANDROID:
        return
    activity = PythonActivity.mActivity
    intent = Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS)
    intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
    activity.startActivity(intent)


def has_usage_stats_permission() -> bool:
    if not _ON_ANDROID:
        return True
    try:
        AppOpsManager   = autoclass("android.app.AppOpsManager")
        Context         = autoclass("android.content.Context")
        activity        = PythonActivity.mActivity
        app_ops         = activity.getSystemService(Context.APP_OPS_SERVICE)
        mode = app_ops.checkOpNoThrow(
            AppOpsManager.OPSTR_GET_USAGE_STATS,
            activity.getApplicationInfo().uid,
            activity.getPackageName(),
        )
        return mode == AppOpsManager.MODE_ALLOWED
    except Exception:
        return False


def request_overlay_permission():
    """Open the overlay (SYSTEM_ALERT_WINDOW) settings screen."""
    if not _ON_ANDROID:
        return
    activity = PythonActivity.mActivity
    intent = Intent(
        Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
        Uri.parse("package:" + activity.getPackageName()),
    )
    intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
    activity.startActivity(intent)


def has_overlay_permission() -> bool:
    if not _ON_ANDROID:
        return True
    try:
        Settings_ = autoclass("android.provider.Settings")
        return Settings_.canDrawOverlays(PythonActivity.mActivity)
    except Exception:
        return False


def request_accessibility_settings():
    """Open the Accessibility settings screen."""
    if not _ON_ANDROID:
        return
    activity = PythonActivity.mActivity
    intent = Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)
    intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
    activity.startActivity(intent)


def check_all_permissions() -> dict:
    return {
        "usage_stats":   has_usage_stats_permission(),
        "overlay":       has_overlay_permission(),
    }
