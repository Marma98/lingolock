package com.lingoblock;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.util.Log;

/**
 * Receives the APP_BLOCKED broadcast from LingoAccessibilityService and
 * (re-)launches PythonActivity with the trigger package extra.
 *
 * Also handles BOOT_COMPLETED to restart the monitor service on boot.
 */
public class OverlayReceiver extends BroadcastReceiver {

    private static final String TAG = "LingoOverlayReceiver";

    @Override
    public void onReceive(Context context, Intent intent) {
        String action = intent.getAction();
        if (action == null) return;

        switch (action) {
            case LingoAccessibilityService.ACTION_APP_BLOCKED:
                handleAppBlocked(context, intent);
                break;
            case Intent.ACTION_BOOT_COMPLETED:
                handleBoot(context);
                break;
            default:
                Log.d(TAG, "Unhandled action: " + action);
        }
    }

    private void handleAppBlocked(Context context, Intent incoming) {
        String pkg = incoming.getStringExtra(LingoAccessibilityService.EXTRA_PACKAGE);
        if (pkg == null || pkg.isEmpty()) return;

        Log.i(TAG, "APP_BLOCKED received for: " + pkg);

        try {
            Class<?> activityClass = Class.forName("org.kivy.android.PythonActivity");
            Intent launch = new Intent(context, activityClass);
            launch.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_REORDER_TO_FRONT);
            launch.putExtra(LingoAccessibilityService.EXTRA_PACKAGE, pkg);
            context.startActivity(launch);
        } catch (ClassNotFoundException e) {
            Log.e(TAG, "PythonActivity not found", e);
        }
    }

    private void handleBoot(Context context) {
        Log.i(TAG, "Boot completed — restarting monitor service");
        try {
            Class<?> serviceClass = Class.forName("org.kivy.android.PythonService");
            Intent service = new Intent(context, serviceClass);
            service.putExtra("androidPrivate", context.getFilesDir().getAbsolutePath());
            service.putExtra("androidArgument", context.getFilesDir().getAbsolutePath());
            service.putExtra("serviceEntrypoint", "services/monitor_service.py");
            service.putExtra("pythonName", "Monitor");
            service.putExtra("pythonHome", context.getFilesDir().getAbsolutePath());
            service.putExtra("pythonPath", context.getFilesDir().getAbsolutePath());
            service.putExtra("serviceTitle", "LingoLock Monitor");
            service.putExtra("serviceDescription", "Blocking active");
            context.startForegroundService(service);
        } catch (ClassNotFoundException e) {
            Log.e(TAG, "PythonService not found", e);
        }
    }
}
