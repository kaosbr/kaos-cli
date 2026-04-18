package com.monster.dpc;

import android.app.admin.DeviceAdminReceiver;
import android.app.admin.DevicePolicyManager;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.provider.Settings;
import android.util.Log;

/**
 * Monster DPC - Advanced MDM/KG Bypass Controller
 * This app is designed to be injected via QR Code Provisioning.
 */
public class MonsterAdminReceiver extends DeviceAdminReceiver {

    @Override
    public void onProfileProvisioningComplete(Context context, Intent intent) {
        // This is called when the QR Code provisioning finishes
        DevicePolicyManager dpm = (DevicePolicyManager) context.getSystemService(Context.DEVICE_POLICY_SERVICE);
        ComponentName adminComponent = new ComponentName(context, MonsterAdminReceiver.class);

        Log.i("MONSTER_DPC", "Provisioning Complete! Assuming Device Owner role.");

        try {
            // 1. Force Enable ADB
            Settings.Global.putInt(context.getContentResolver(), Settings.Global.ADB_ENABLED, 1);
            Log.i("MONSTER_DPC", "ADB has been forcefully enabled.");

            // 2. Disable Keyguard (Lockscreen)
            dpm.setKeyguardDisabled(adminComponent, true);

            // 3. Disable System Updates (To prevent Knox Guard from updating)
            dpm.setSystemUpdatePolicy(adminComponent, null);

            // 4. Stay Awake while plugged in
            Settings.Global.putInt(context.getContentResolver(), Settings.Global.STAY_ON_WHILE_PLUGGED_IN, 3);

        } catch (Exception e) {
            Log.e("MONSTER_DPC", "Error during bypass: " + e.getMessage());
        }
    }

    @Override
    public void onEnabled(Context context, Intent intent) {
        super.onEnabled(context, intent);
        Log.i("MONSTER_DPC", "Monster DPC is now Device Owner.");
    }
}
