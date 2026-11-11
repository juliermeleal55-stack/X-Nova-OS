.class public Lio/mesalabs/unica/settings/DeveloperOptionsPreferenceController;
.super Lcom/android/settings/core/TogglePreferenceController;
.source "DeveloperOptionsPreferenceController.java"

.method public constructor <init>(Landroid/content/Context;Ljava/lang/String;)V
    .locals 2

    invoke-direct {p0, p1, p2}, Lcom/android/settings/core/TogglePreferenceController;-><init>(Landroid/content/Context;Ljava/lang/String;)V

    invoke-virtual {p1}, Landroid/content/Context;->getContentResolver()Landroid/content/ContentResolver;
    move-result-object p2
    const-string v0, "development_settings_enabled"
    invoke-static {p2, v0}, Landroid/provider/Settings$Global;->getString(Landroid/content/ContentResolver;Ljava/lang/String;)Ljava/lang/String;
    move-result-object p2
    if-nez p2, :done

    const/4 v1, 0x1
    invoke-static {p1, v1}, Lcom/android/settingslib/development/DevelopmentSettingsEnabler;->setDevelopmentSettingsEnabled(Landroid/content/Context;Z)V

    :done
    return-void
.end method

.method public getAvailabilityStatus()I
    .locals 3
    iget-object v0, p0, Lcom/android/settingslib/core/AbstractPreferenceController;->mContext:Landroid/content/Context;
    invoke-virtual {v0}, Landroid/content/Context;->getContentResolver()Landroid/content/ContentResolver;
    move-result-object v0
    const-string v1, "onerom_show_developer_options"
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

.method public isChecked()Z
    .locals 1
    iget-object v0, p0, Lcom/android/settingslib/core/AbstractPreferenceController;->mContext:Landroid/content/Context;
    invoke-static {v0}, Lcom/android/settingslib/development/DevelopmentSettingsEnabler;->isDevelopmentSettingsEnabled(Landroid/content/Context;)Z
    move-result v0
    return v0
.end method

.method public setChecked(Z)Z
    .locals 1
    iget-object v0, p0, Lcom/android/settingslib/core/AbstractPreferenceController;->mContext:Landroid/content/Context;
    invoke-static {v0, p1}, Lcom/android/settingslib/development/DevelopmentSettingsEnabler;->setDevelopmentSettingsEnabled(Landroid/content/Context;Z)V
    const/4 v0, 0x1
    return v0
.end method
