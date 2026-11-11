.class public Lio/mesalabs/unica/settings/GenericTogglePreferenceController;
.super Lcom/android/settings/core/TogglePreferenceController;

.method public constructor <init>(Landroid/content/Context;Ljava/lang/String;)V
    .locals 0
    invoke-direct {p0, p1, p2}, Lcom/android/settings/core/TogglePreferenceController;-><init>(Landroid/content/Context;Ljava/lang/String;)V
    return-void
.end method

.method public getAvailabilityStatus()I
    .locals 1
    const/4 v0, 0x0
    return v0
.end method

.method public isChecked()Z
    .locals 3
    iget-object v0, p0, Lcom/android/settingslib/core/AbstractPreferenceController;->mContext:Landroid/content/Context;
    invoke-virtual {v0}, Landroid/content/Context;->getContentResolver()Landroid/content/ContentResolver;
    move-result-object v0
    iget-object v1, p0, Lcom/android/settings/core/BasePreferenceController;->mPreferenceKey:Ljava/lang/String;
    const/4 v2, 0x1
    invoke-static {v0, v1, v2}, Landroid/provider/Settings$System;->getInt(Landroid/content/ContentResolver;Ljava/lang/String;I)I
    move-result v0
    if-eqz v0, :disabled
    const/4 v0, 0x1
    return v0
    :disabled
    const/4 v0, 0x0
    return v0
.end method

.method public setChecked(Z)Z
    .locals 3
    iget-object v0, p0, Lcom/android/settingslib/core/AbstractPreferenceController;->mContext:Landroid/content/Context;
    invoke-virtual {v0}, Landroid/content/Context;->getContentResolver()Landroid/content/ContentResolver;
    move-result-object v0
    iget-object v1, p0, Lcom/android/settings/core/BasePreferenceController;->mPreferenceKey:Ljava/lang/String;
    invoke-static {v0, v1, p1}, Landroid/provider/Settings$System;->putInt(Landroid/content/ContentResolver;Ljava/lang/String;I)Z

    const-string v0, "onerom_show_"
    invoke-virtual {v1, v0}, Ljava/lang/String;->startsWith(Ljava/lang/String;)Z
    move-result v0
    if-eqz v0, :done_spoof_check
    const/4 v0, 0x1
    sput-boolean v0, Lio/mesalabs/unica/settings/spoof/SpoofSettingsFragment;->sNeedsAboutPhoneRestart:Z

    :done_spoof_check
    const/4 v0, 0x1
    return v0
.end method
