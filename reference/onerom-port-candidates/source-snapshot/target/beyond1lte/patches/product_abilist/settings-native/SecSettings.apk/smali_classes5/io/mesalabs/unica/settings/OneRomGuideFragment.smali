.class public Lio/mesalabs/unica/settings/OneRomGuideFragment;
.super Lcom/android/settings/dashboard/DashboardFragment;
.source "OneRomGuideFragment.java"


# direct methods
.method public constructor <init>()V
    .registers 1

    invoke-direct {p0}, Lcom/android/settings/dashboard/DashboardFragment;-><init>()V

    return-void
.end method


# virtual methods
.method public final getLogTag()Ljava/lang/String;
    .registers 2

    const-string v0, "OneROMGuide"

    return-object v0
.end method

.method public final getMetricsCategory()I
    .registers 2

    const/16 v0, 0x2e8

    return v0
.end method

.method public final getPreferenceScreenResId()I
    .registers 2

    const-string/jumbo p0, "xml"

    const-string v0, "onerom_guide"

    invoke-static {p0, v0}, Lio/mesalabs/unica/utils/Utils;->getResourceId(Ljava/lang/String;Ljava/lang/String;)I

    move-result p0

    return p0
.end method

.method public onCreatePreferences(Landroid/os/Bundle;Ljava/lang/String;)V
    .registers 8

    invoke-virtual {p0}, Landroidx/preference/PreferenceFragmentCompat;->getPreferenceManager()Landroidx/preference/PreferenceManager;

    move-result-object p1

    invoke-virtual {p0}, Landroidx/fragment/app/Fragment;->getContext()Landroid/content/Context;

    move-result-object p2

    invoke-virtual {p1, p2}, Landroidx/preference/PreferenceManager;->createPreferenceScreen(Landroid/content/Context;)Landroidx/preference/PreferenceScreen;

    move-result-object p1

    new-instance v0, Landroidx/preference/PreferenceCategory;

    invoke-direct {v0, p2}, Landroidx/preference/PreferenceCategory;-><init>(Landroid/content/Context;)V

    const-string v1, "OneROM 9.0 Information"

    invoke-virtual {v0, v1}, Landroidx/preference/Preference;->setTitle(Ljava/lang/CharSequence;)V

    invoke-virtual {p1, v0}, Landroidx/preference/PreferenceGroup;->addPreference(Landroidx/preference/Preference;)Z

    new-instance v1, Landroidx/preference/Preference;

    invoke-direct {v1, p2}, Landroidx/preference/Preference;-><init>(Landroid/content/Context;)V

    const/4 v2, 0x0

    invoke-virtual {v1, v2}, Landroidx/preference/Preference;->setSelectable(Z)V

    const-string v3, "Release Overview"

    invoke-virtual {v1, v3}, Landroidx/preference/Preference;->setTitle(Ljava/lang/CharSequence;)V

    const-string v3, "Welcome to OneROM 9.0 for Samsung Galaxy S10 (beyond1lte). High-performance custom ROM powered by One UI 9.0 (Android 17)."

    invoke-virtual {v1, v3}, Landroidx/preference/Preference;->setSummary(Ljava/lang/CharSequence;)V

    invoke-virtual {v0, v1}, Landroidx/preference/PreferenceGroup;->addPreference(Landroidx/preference/Preference;)Z

    new-instance v1, Landroidx/preference/Preference;

    invoke-direct {v1, p2}, Landroidx/preference/Preference;-><init>(Landroid/content/Context;)V

    const-string v3, "Telegram Support (@DaManMikey)"

    invoke-virtual {v1, v3}, Landroidx/preference/Preference;->setTitle(Ljava/lang/CharSequence;)V

    const-string v3, "Tap to open Telegram and contact @DaManMikey directly for support and bug reports."

    invoke-virtual {v1, v3}, Landroidx/preference/Preference;->setSummary(Ljava/lang/CharSequence;)V

    new-instance v3, Landroid/content/Intent;

    const-string v4, "android.intent.action.VIEW"

    const-string v2, "https://t.me/DaManMikey"

    invoke-static {v2}, Landroid/net/Uri;->parse(Ljava/lang/String;)Landroid/net/Uri;

    move-result-object v2

    invoke-direct {v3, v4, v2}, Landroid/content/Intent;-><init>(Ljava/lang/String;Landroid/net/Uri;)V

    invoke-virtual {v1, v3}, Landroidx/preference/Preference;->setIntent(Landroid/content/Intent;)V

    invoke-virtual {v0, v1}, Landroidx/preference/PreferenceGroup;->addPreference(Landroidx/preference/Preference;)Z

    new-instance v0, Landroidx/preference/PreferenceCategory;

    invoke-direct {v0, p2}, Landroidx/preference/PreferenceCategory;-><init>(Landroid/content/Context;)V

    const-string v1, "Navigation & Gestures"

    invoke-virtual {v0, v1}, Landroidx/preference/Preference;->setTitle(Ljava/lang/CharSequence;)V

    invoke-virtual {p1, v0}, Landroidx/preference/PreferenceGroup;->addPreference(Landroidx/preference/Preference;)Z

    new-instance v1, Landroidx/preference/Preference;

    invoke-direct {v1, p2}, Landroidx/preference/Preference;-><init>(Landroid/content/Context;)V

    const/4 v2, 0x0

    invoke-virtual {v1, v2}, Landroidx/preference/Preference;->setSelectable(Z)V

    const-string v3, "Quick Shortcuts"

    invoke-virtual {v1, v3}, Landroidx/preference/Preference;->setTitle(Ljava/lang/CharSequence;)V

    const-string v3, "Tap About phone once for device details, double-tap for Software information, or hold it down to launch Developer options."

    invoke-virtual {v1, v3}, Landroidx/preference/Preference;->setSummary(Ljava/lang/CharSequence;)V

    invoke-virtual {v0, v1}, Landroidx/preference/PreferenceGroup;->addPreference(Landroidx/preference/Preference;)Z

    new-instance v1, Landroidx/preference/Preference;

    invoke-direct {v1, p2}, Landroidx/preference/Preference;-><init>(Landroid/content/Context;)V

    invoke-virtual {v1, v2}, Landroidx/preference/Preference;->setSelectable(Z)V

    const-string v3, "Extra options"

    invoke-virtual {v1, v3}, Landroidx/preference/Preference;->setTitle(Ljava/lang/CharSequence;)V

    const-string v3, "Personalize your device with OneROM Settings: adjust launcher animations, customize status banners, and remap the Bixby button."

    invoke-virtual {v1, v3}, Landroidx/preference/Preference;->setSummary(Ljava/lang/CharSequence;)V

    invoke-virtual {v0, v1}, Landroidx/preference/PreferenceGroup;->addPreference(Landroidx/preference/Preference;)Z

    new-instance v0, Landroidx/preference/PreferenceCategory;

    invoke-direct {v0, p2}, Landroidx/preference/PreferenceCategory;-><init>(Landroid/content/Context;)V

    const-string v1, "OneROM 9.0 Features"

    invoke-virtual {v0, v1}, Landroidx/preference/Preference;->setTitle(Ljava/lang/CharSequence;)V

    invoke-virtual {p1, v0}, Landroidx/preference/PreferenceGroup;->addPreference(Landroidx/preference/Preference;)Z

    new-instance v1, Landroidx/preference/Preference;

    invoke-direct {v1, p2}, Landroidx/preference/Preference;-><init>(Landroid/content/Context;)V

    invoke-virtual {v1, v2}, Landroidx/preference/Preference;->setSelectable(Z)V

    const-string v3, "Ultrasonic Fingerprint (FOD)"

    invoke-virtual {v1, v3}, Landroidx/preference/Preference;->setTitle(Ljava/lang/CharSequence;)V

    const-string v3, "Calibrated for Galaxy S10 Qualcomm ultrasonic hardware. Keep your finger pressed firmly against the scanner for instant unlock."

    invoke-virtual {v1, v3}, Landroidx/preference/Preference;->setSummary(Ljava/lang/CharSequence;)V

    invoke-virtual {v0, v1}, Landroidx/preference/PreferenceGroup;->addPreference(Landroidx/preference/Preference;)Z

    new-instance v1, Landroidx/preference/Preference;

    invoke-direct {v1, p2}, Landroidx/preference/Preference;-><init>(Landroid/content/Context;)V

    invoke-virtual {v1, v2}, Landroidx/preference/Preference;->setSelectable(Z)V

    const-string v3, "Samsung Native AppLock"

    invoke-virtual {v1, v3}, Landroidx/preference/Preference;->setTitle(Ljava/lang/CharSequence;)V

    const-string v3, "Lock any installed application securely with your fingerprint or PIN from Settings > Advanced Features > AppLock."

    invoke-virtual {v1, v3}, Landroidx/preference/Preference;->setSummary(Ljava/lang/CharSequence;)V

    invoke-virtual {v0, v1}, Landroidx/preference/PreferenceGroup;->addPreference(Landroidx/preference/Preference;)Z

    new-instance v1, Landroidx/preference/Preference;

    invoke-direct {v1, p2}, Landroidx/preference/Preference;-><init>(Landroid/content/Context;)V

    invoke-virtual {v1, v2}, Landroidx/preference/Preference;->setSelectable(Z)V

    const-string v3, "Battery Health (BSOH)"

    invoke-virtual {v1, v3}, Landroidx/preference/Preference;->setTitle(Ljava/lang/CharSequence;)V

    const-string v3, "Inspect battery health state and charging protection limits under Settings > Battery > Battery Information."

    invoke-virtual {v1, v3}, Landroidx/preference/Preference;->setSummary(Ljava/lang/CharSequence;)V

    invoke-virtual {v0, v1}, Landroidx/preference/PreferenceGroup;->addPreference(Landroidx/preference/Preference;)Z

    new-instance v1, Landroidx/preference/Preference;

    invoke-direct {v1, p2}, Landroidx/preference/Preference;-><init>(Landroid/content/Context;)V

    invoke-virtual {v1, v2}, Landroidx/preference/Preference;->setSelectable(Z)V

    const-string v3, "KernelSU-Next Root"

    invoke-virtual {v1, v3}, Landroidx/preference/Preference;->setTitle(Ljava/lang/CharSequence;)V

    const-string v3, "Integrated kernel-level root via OneKernel with KernelSU Next and userspace ksud daemon."

    invoke-virtual {v1, v3}, Landroidx/preference/Preference;->setSummary(Ljava/lang/CharSequence;)V

    invoke-virtual {v0, v1}, Landroidx/preference/PreferenceGroup;->addPreference(Landroidx/preference/Preference;)Z

    new-instance v1, Landroidx/preference/Preference;

    invoke-direct {v1, p2}, Landroidx/preference/Preference;-><init>(Landroid/content/Context;)V

    invoke-virtual {v1, v2}, Landroidx/preference/Preference;->setSelectable(Z)V

    const-string v3, "Hardware & Privacy"

    invoke-virtual {v1, v3}, Landroidx/preference/Preference;->setTitle(Ljava/lang/CharSequence;)V

    const-string v3, "Full Exynos 9820 Hardware Composer integration and privacy toggles to mask IMEI and Serial Number in Extra Settings."

    invoke-virtual {v1, v3}, Landroidx/preference/Preference;->setSummary(Ljava/lang/CharSequence;)V

    invoke-virtual {v0, v1}, Landroidx/preference/PreferenceGroup;->addPreference(Landroidx/preference/Preference;)Z

    new-instance v0, Landroidx/preference/PreferenceCategory;

    invoke-direct {v0, p2}, Landroidx/preference/PreferenceCategory;-><init>(Landroid/content/Context;)V

    const-string v1, "Looking for something else?"

    invoke-virtual {v0, v1}, Landroidx/preference/Preference;->setTitle(Ljava/lang/CharSequence;)V

    invoke-virtual {p1, v0}, Landroidx/preference/PreferenceGroup;->addPreference(Landroidx/preference/Preference;)Z

    new-instance v1, Landroidx/preference/Preference;

    invoke-direct {v1, p2}, Landroidx/preference/Preference;-><init>(Landroid/content/Context;)V

    const-string v3, "Software information"

    invoke-virtual {v1, v3}, Landroidx/preference/Preference;->setTitle(Ljava/lang/CharSequence;)V

    const-string v3, "com.samsung.android.settings.deviceinfo.softwareinfo.SoftwareInfoSettings"

    invoke-virtual {v1, v3}, Landroidx/preference/Preference;->setFragment(Ljava/lang/String;)V

    invoke-virtual {v0, v1}, Landroidx/preference/PreferenceGroup;->addPreference(Landroidx/preference/Preference;)Z

    new-instance v1, Landroidx/preference/Preference;

    invoke-direct {v1, p2}, Landroidx/preference/Preference;-><init>(Landroid/content/Context;)V

    const-string v3, "OneROM Settings"

    invoke-virtual {v1, v3}, Landroidx/preference/Preference;->setTitle(Ljava/lang/CharSequence;)V

    const-string v3, "io.mesalabs.unica.settings.UnicaSettingsFragment"

    invoke-virtual {v1, v3}, Landroidx/preference/Preference;->setFragment(Ljava/lang/String;)V

    invoke-virtual {v0, v1}, Landroidx/preference/PreferenceGroup;->addPreference(Landroidx/preference/Preference;)Z

    new-instance v1, Landroidx/preference/Preference;

    invoke-direct {v1, p2}, Landroidx/preference/Preference;-><init>(Landroid/content/Context;)V

    const-string v3, "OneROM changelog"

    invoke-virtual {v1, v3}, Landroidx/preference/Preference;->setTitle(Ljava/lang/CharSequence;)V

    const-string v3, "io.mesalabs.unica.settings.ChangelogFragment"

    invoke-virtual {v1, v3}, Landroidx/preference/Preference;->setFragment(Ljava/lang/String;)V

    invoke-virtual {v0, v1}, Landroidx/preference/PreferenceGroup;->addPreference(Landroidx/preference/Preference;)Z

    invoke-virtual {p0, p1}, Landroidx/preference/PreferenceFragmentCompat;->setPreferenceScreen(Landroidx/preference/PreferenceScreen;)V

    return-void
.end method
