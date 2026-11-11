package com.android.internal.os;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.security.GeneralSecurityException;
import java.security.MessageDigest;

public final class S10AppCodeOverrides {
    private S10AppCodeOverrides() {}

    public static String get(String dexPath) {
        if (dexPath == null) {
            return null;
        }
        String[] allowed = {
            "/system/priv-app/SettingsProvider/SettingsProvider.apk",
            "/system/priv-app/SecSettings/SecSettings.apk",
            "/system/priv-app/BiometricSetting/BiometricSetting.apk",
            "/system/system_ext/priv-app/SystemUI/SystemUI.apk",
            "/system_ext/priv-app/SystemUI/SystemUI.apk"
        };
        for (String source : allowed) {
            if (!source.equals(dexPath)) {
                continue;
            }
            File apk = new File(source);
            File directory = new File("/system/framework/s10-app-overrides", apk.getName());
            File code = new File(directory, "classes.jar");
            if (code.isFile() && matches(apk, new File(directory, "apk.sha256"))) {
                return code.getPath() + File.pathSeparator + dexPath;
            }
            break;
        }
        return dexPath;
    }

    static boolean matches(File apk, File marker) {
        try {
            if (marker.length() > 128) {
                return false;
            }
            String expected = new String(Files.readAllBytes(marker.toPath()), StandardCharsets.US_ASCII).trim();
            if (!expected.matches("[0-9a-f]{64}")) {
                return false;
            }
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            try (FileInputStream input = new FileInputStream(apk)) {
                byte[] buffer = new byte[32768];
                int count;
                while ((count = input.read(buffer)) != -1) {
                    digest.update(buffer, 0, count);
                }
            }
            StringBuilder actual = new StringBuilder(64);
            for (byte value : digest.digest()) {
                actual.append(Character.forDigit((value >>> 4) & 15, 16));
                actual.append(Character.forDigit(value & 15, 16));
            }
            return expected.equals(actual.toString());
        } catch (IOException | GeneralSecurityException | RuntimeException error) {
            return false;
        }
    }
}