.class public Lio/mesalabs/unica/settings/DoubleTapAboutPreferenceController;
.super Lcom/android/settings/core/BasePreferenceController;
.source "DoubleTapAboutPreferenceController.java"

.implements Landroidx/preference/Preference$OnPreferenceClickListener;

.field public mHandler:Landroid/os/Handler;
.field public mPending:Z
.field public mSingleTap:Ljava/lang/Runnable;

.method public constructor <init>(Landroid/content/Context;Ljava/lang/String;)V
    .locals 1
    invoke-direct {p0, p1, p2}, Lcom/android/settings/core/BasePreferenceController;-><init>(Landroid/content/Context;Ljava/lang/String;)V
    new-instance p1, Landroid/os/Handler;
    invoke-static {}, Landroid/os/Looper;->getMainLooper()Landroid/os/Looper;
    move-result-object p2
    invoke-direct {p1, p2}, Landroid/os/Handler;-><init>(Landroid/os/Looper;)V
    iput-object p1, p0, Lio/mesalabs/unica/settings/DoubleTapAboutPreferenceController;->mHandler:Landroid/os/Handler;
    new-instance p1, Lio/mesalabs/unica/settings/DoubleTapAboutPreferenceController$1;
    invoke-direct {p1, p0}, Lio/mesalabs/unica/settings/DoubleTapAboutPreferenceController$1;-><init>(Lio/mesalabs/unica/settings/DoubleTapAboutPreferenceController;)V
    iput-object p1, p0, Lio/mesalabs/unica/settings/DoubleTapAboutPreferenceController;->mSingleTap:Ljava/lang/Runnable;
    return-void
.end method

.method public displayPreference(Landroidx/preference/PreferenceScreen;)V
    .locals 2
    invoke-super {p0, p1}, Lcom/android/settings/core/BasePreferenceController;->displayPreference(Landroidx/preference/PreferenceScreen;)V
    iget-object v0, p0, Lcom/android/settings/core/BasePreferenceController;->mPreferenceKey:Ljava/lang/String;
    invoke-virtual {p1, v0}, Landroidx/preference/PreferenceGroup;->findPreference(Ljava/lang/CharSequence;)Landroidx/preference/Preference;
    move-result-object v0
    const/4 v1, 0x0
    invoke-virtual {v0, v1}, Landroidx/preference/Preference;->setFragment(Ljava/lang/String;)V
    invoke-virtual {v0, p0}, Landroidx/preference/Preference;->setOnPreferenceClickListener(Landroidx/preference/Preference$OnPreferenceClickListener;)V
    return-void
.end method

.method public getAvailabilityStatus()I
    .locals 1
    const/4 v0, 0x0
    return v0
.end method

.method public getSummary()Ljava/lang/CharSequence;
    .locals 5

    invoke-static {}, Lcom/samsung/android/feature/SemFloatingFeature;->getInstance()Lcom/samsung/android/feature/SemFloatingFeature;
    move-result-object v0
    const-string v1, "SEC_FLOATING_FEATURE_SETTINGS_CONFIG_BRAND_NAME"
    invoke-virtual {v0, v1}, Lcom/samsung/android/feature/SemFloatingFeature;->getString(Ljava/lang/String;)Ljava/lang/String;
    move-result-object v0
    invoke-static {v0}, Landroid/text/TextUtils;->isEmpty(Ljava/lang/CharSequence;)Z
    move-result v1
    if-eqz v1, :model_ready
    sget-object v0, Landroid/os/Build;->MODEL:Ljava/lang/String;

    :model_ready
    new-instance v1, Lcom/samsung/android/settings/deviceinfo/softwareinfo/OneUIVersionPreferenceController;
    iget-object v2, p0, Lcom/android/settingslib/core/AbstractPreferenceController;->mContext:Landroid/content/Context;
    const-string v3, "one_ui_version"
    invoke-direct {v1, v2, v3}, Lcom/samsung/android/settings/deviceinfo/softwareinfo/OneUIVersionPreferenceController;-><init>(Landroid/content/Context;Ljava/lang/String;)V
    invoke-virtual {v1}, Lcom/samsung/android/settings/deviceinfo/softwareinfo/OneUIVersionPreferenceController;->getSummary()Ljava/lang/CharSequence;
    move-result-object v1

    new-instance v2, Ljava/lang/StringBuilder;
    invoke-direct {v2}, Ljava/lang/StringBuilder;-><init>()V
    invoke-virtual {v2, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    const-string v0, "    \u2022    One UI "
    invoke-virtual {v2, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v2, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/Object;)Ljava/lang/StringBuilder;
    invoke-virtual {v2}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v0
    return-object v0
.end method

.method public launchDestination(Ljava/lang/String;)V
    .locals 2
    new-instance v0, Lcom/android/settings/core/SubSettingLauncher;
    iget-object v1, p0, Lcom/android/settingslib/core/AbstractPreferenceController;->mContext:Landroid/content/Context;
    invoke-direct {v0, v1}, Lcom/android/settings/core/SubSettingLauncher;-><init>(Landroid/content/Context;)V
    iget-object v1, v0, Lcom/android/settings/core/SubSettingLauncher;->mLaunchRequest:Lcom/android/settings/core/SubSettingLauncher$LaunchRequest;
    iput-object p1, v1, Lcom/android/settings/core/SubSettingLauncher$LaunchRequest;->mDestinationName:Ljava/lang/String;
    const/16 p1, 0x28
    iput p1, v1, Lcom/android/settings/core/SubSettingLauncher$LaunchRequest;->mSourceMetricsCategory:I
    invoke-virtual {v0}, Lcom/android/settings/core/SubSettingLauncher;->launch()V
    return-void
.end method

.method public onPreferenceClick(Landroidx/preference/Preference;)Z
    .locals 5
    iget-boolean v0, p0, Lio/mesalabs/unica/settings/DoubleTapAboutPreferenceController;->mPending:Z
    if-eqz v0, :first_tap
    iget-object v0, p0, Lio/mesalabs/unica/settings/DoubleTapAboutPreferenceController;->mHandler:Landroid/os/Handler;
    iget-object v1, p0, Lio/mesalabs/unica/settings/DoubleTapAboutPreferenceController;->mSingleTap:Ljava/lang/Runnable;
    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V
    const/4 v0, 0x0
    iput-boolean v0, p0, Lio/mesalabs/unica/settings/DoubleTapAboutPreferenceController;->mPending:Z
    const-string v0, "com.samsung.android.settings.deviceinfo.softwareinfo.SoftwareInfoSettings"
    invoke-virtual {p0, v0}, Lio/mesalabs/unica/settings/DoubleTapAboutPreferenceController;->launchDestination(Ljava/lang/String;)V
    const/4 v0, 0x1
    return v0

    :first_tap
    const/4 v0, 0x1
    iput-boolean v0, p0, Lio/mesalabs/unica/settings/DoubleTapAboutPreferenceController;->mPending:Z
    iget-object v1, p0, Lio/mesalabs/unica/settings/DoubleTapAboutPreferenceController;->mHandler:Landroid/os/Handler;
    iget-object v2, p0, Lio/mesalabs/unica/settings/DoubleTapAboutPreferenceController;->mSingleTap:Ljava/lang/Runnable;
    const-wide/16 v3, 0x140
    invoke-virtual {v1, v2, v3, v4}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z
    return v0
.end method
