.class public Lio/mesalabs/unica/settings/extra/ImeiVisibilityPreferenceController;
.super Lcom/android/settings/core/BasePreferenceController;
.source "ImeiVisibilityPreferenceController.java"

.method public constructor <init>(Landroid/content/Context;Ljava/lang/String;)V
    .locals 0
    invoke-direct {p0, p1, p2}, Lcom/android/settings/core/BasePreferenceController;-><init>(Landroid/content/Context;Ljava/lang/String;)V
    return-void
.end method

.method public getAvailabilityStatus()I
    .locals 4
    iget-object v0, p0, Lcom/android/settingslib/core/AbstractPreferenceController;->mContext:Landroid/content/Context;
    invoke-virtual {v0}, Landroid/content/Context;->getContentResolver()Landroid/content/ContentResolver;
    move-result-object v1
    const-string v2, "onerom_show_imei"
    const/4 v3, 0x1
    invoke-static {v1, v2, v3}, Landroid/provider/Settings$System;->getInt(Landroid/content/ContentResolver;Ljava/lang/String;I)I
    move-result v1
    if-eqz v1, :hidden
    invoke-static {v0}, Lcom/android/settingslib/Utils;->isWifiOnly(Landroid/content/Context;)Z
    move-result v0
    if-nez v0, :hidden
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

    invoke-virtual {p0}, Lio/mesalabs/unica/settings/extra/ImeiVisibilityPreferenceController;->getAvailabilityStatus()I
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
