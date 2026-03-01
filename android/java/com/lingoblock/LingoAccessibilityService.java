package com.lingoblock;

import android.accessibilityservice.AccessibilityService;
import android.accessibilityservice.AccessibilityServiceInfo;
import android.content.Intent;
import android.util.Log;
import android.view.accessibility.AccessibilityEvent;

import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;

/**
 * Detects when a blocked app comes to the foreground and broadcasts
 * an intent to trigger the challenge overlay.
 *
 * Registered in the manifest via extra_manifest_application.xml.
 */
public class LingoAccessibilityService extends AccessibilityService {

    private static final String TAG = "LingoAccService";
    public  static final String ACTION_APP_BLOCKED = "com.lingoblock.APP_BLOCKED";
    public  static final String EXTRA_PACKAGE      = "trigger_package";

    /** Default blocked packages — kept in sync with DB seed data. */
    private static final Set<String> BLOCKED_PACKAGES = new HashSet<>(Arrays.asList(
            "com.instagram.android",
            "com.zhiliaoapp.musically",
            "com.facebook.katana",
            "com.twitter.android",
            "com.snapchat.android",
            "com.reddit.frontpage"
    ));

    private String  lastBlockedPackage = null;
    private long    lastBroadcastMs    = 0L;
    private static final long COOLDOWN_MS = 10_000L;

    // ── AccessibilityService lifecycle ────────────────────────────────────────

    @Override
    public void onServiceConnected() {
        AccessibilityServiceInfo info = new AccessibilityServiceInfo();
        info.eventTypes = AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED;
        info.feedbackType = AccessibilityServiceInfo.FEEDBACK_GENERIC;
        info.flags = AccessibilityServiceInfo.FLAG_INCLUDE_NOT_IMPORTANT_VIEWS;
        info.notificationTimeout = 100;
        setServiceInfo(info);
        Log.i(TAG, "Accessibility service connected");
    }

    @Override
    public void onAccessibilityEvent(AccessibilityEvent event) {
        if (event.getEventType() != AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED) return;

        CharSequence pkg = event.getPackageName();
        if (pkg == null) return;

        String packageName = pkg.toString();

        // Skip our own package to avoid re-triggering
        if (packageName.equals(getPackageName())) return;

        if (!BLOCKED_PACKAGES.contains(packageName)) return;

        long now = System.currentTimeMillis();
        if (packageName.equals(lastBlockedPackage) && (now - lastBroadcastMs) < COOLDOWN_MS) {
            return;  // still in cooldown
        }

        lastBlockedPackage = packageName;
        lastBroadcastMs    = now;

        Log.i(TAG, "Blocked app detected: " + packageName);
        broadcastBlock(packageName);
        launchChallenge(packageName);
    }

    @Override
    public void onInterrupt() {
        Log.w(TAG, "Accessibility service interrupted");
    }

    // ── Helpers ───────────────────────────────────────────────────────────────

    private void broadcastBlock(String packageName) {
        Intent broadcast = new Intent(ACTION_APP_BLOCKED);
        broadcast.putExtra(EXTRA_PACKAGE, packageName);
        broadcast.setPackage(getPackageName());
        sendBroadcast(broadcast);
    }

    private void launchChallenge(String packageName) {
        try {
            Class<?> activityClass = Class.forName("org.kivy.android.PythonActivity");
            Intent intent = new Intent(this, activityClass);
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_REORDER_TO_FRONT);
            intent.putExtra(EXTRA_PACKAGE, packageName);
            startActivity(intent);
        } catch (ClassNotFoundException e) {
            Log.e(TAG, "PythonActivity not found", e);
        }
    }
}
