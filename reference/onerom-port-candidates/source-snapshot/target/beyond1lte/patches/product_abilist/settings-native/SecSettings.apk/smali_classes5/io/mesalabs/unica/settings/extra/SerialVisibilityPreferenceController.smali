.class public Lio/mesalabs/unica/settings/extra/SerialVisibilityPreferenceController;
.super Lcom/android/settings/core/BasePreferenceController;
.source "SerialVisibilityPreferenceController.java"

.method public constructor <init>(Landroid/content/Context;Ljava/lang/String;)V
    .locals 0
    invoke-direct {p0, p1, p2}, Lcom/android/settings/core/BasePreferenceController;-><init>(Landroid/content/Context;Ljava/lang/String;)V
    return-void
.end method

.method public getAvailabilityStatus()I
    .locals 3
    iget-object v0, p0, Lcom/android/settingslib/core/AbstractPreferenceController;->mContext:Landroid/content/Context;
    invoke-virtual {v0}, Landroid/content/Context;->getContentResolver()Landroid/content/ContentResolver;
    move-result-object v0
    const-string v1, "onerom_show_serial"
    const/4 v2, 0x1
    invoke-static {v0, v1, v2}, Landroid/provider/Settings$System;->getInt(Landroid/content/ContentResolver;Ljava/lang/String;I)I
    move-result v0
    if-eqz v0, :hidden
    const/4 v0, 0x0
    return v0
    :hidden
    const/4 v0, 0x3
    return v0
.end method

.method public displayPreference(Landroidx/preference/PreferenceScreen;)V
    .locals 2

    invoke-super {p0, p1}, Lcom/android/settings/core/BasePreferenceController;->displayPreference(Landroidx/preference/PreferenceScreen;)V

    invoke-virtual {p0}, Lcom/android/settings/core/BasePreferenceController;->getPreferenceKey()Ljava/lang/String;
    move-result-object v0
    invoke-virtual {p1, v0}, Landroidx/preference/PreferenceGroup;->findPreference(Ljava/lang/CharSequence;)Landroidx/preference/Preference;
    move-result-object p1
    if-eqz p1, :done

    invoke-virtual {p0}, Lio/mesalabs/unica/settings/extra/SerialVisibilityPreferenceController;->getAvailabilityStatus()I
    move-result v0
    if-nez v0, :hidden
    const/4 v1, 0x1
    goto :apply
    :hidden
    const/4 v1, 0x0
    :apply
    invoke-virtual {p1, v1}, Landroidx/preference/Preference;->setVisible(Z)V

    :done
    return-void
.end method

.method public getSummary()Ljava/lang/CharSequence;
    .locals 1
    iget-object v0, p0, Lcom/android/settingslib/core/AbstractPreferenceController;->mContext:Landroid/content/Context;
    invoke-static {v0}, Lcom/samsung/android/settings/deviceinfo/SecDeviceInfoUtils;->getSerialNumber(Landroid/content/Context;)Ljava/lang/String;
    move-result-object v0
    return-object v0
.end method

.method public useDynamicSliceSummary()Z
    .locals 1
    const/4 v0, 0x1
    return v0
.end method