.class public Lio/mesalabs/unica/settings/BackupRestorePreferenceController;
.super Lcom/android/settings/core/BasePreferenceController;
.source "BackupRestorePreferenceController.java"

.method public constructor <init>(Landroid/content/Context;Ljava/lang/String;)V
    .locals 0
    invoke-direct {p0, p1, p2}, Lcom/android/settings/core/BasePreferenceController;-><init>(Landroid/content/Context;Ljava/lang/String;)V
    return-void
.end method

.method private getBackupFile()Ljava/io/File;
    .locals 3
    new-instance v0, Ljava/io/File;
    invoke-static {}, Landroid/os/Environment;->getExternalStorageDirectory()Ljava/io/File;
    move-result-object v1
    const-string v2, "OneROM"
    invoke-direct {v0, v1, v2}, Ljava/io/File;-><init>(Ljava/io/File;Ljava/lang/String;)V
    invoke-virtual {v0}, Ljava/io/File;->mkdirs()Z
    new-instance v1, Ljava/io/File;
    const-string v2, "onerom-settings.properties"
    invoke-direct {v1, v0, v2}, Ljava/io/File;-><init>(Ljava/io/File;Ljava/lang/String;)V
    return-object v1
.end method

.method private static saveSystem(Ljava/util/Properties;Landroid/content/ContentResolver;Ljava/lang/String;)V
    .locals 1
    invoke-static {p1, p2}, Landroid/provider/Settings$System;->getString(Landroid/content/ContentResolver;Ljava/lang/String;)Ljava/lang/String;
    move-result-object v0
    if-eqz v0, :done
    invoke-virtual {p0, p2, v0}, Ljava/util/Properties;->setProperty(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/Object;
    :done
    return-void
.end method

.method private static restoreSystem(Ljava/util/Properties;Landroid/content/ContentResolver;Ljava/lang/String;)V
    .locals 1
    invoke-virtual {p0, p2}, Ljava/util/Properties;->getProperty(Ljava/lang/String;)Ljava/lang/String;
    move-result-object v0
    if-eqz v0, :done
    invoke-static {p1, p2, v0}, Landroid/provider/Settings$System;->putString(Landroid/content/ContentResolver;Ljava/lang/String;Ljava/lang/String;)Z
    :done
    return-void
.end method

.method private showToast(Ljava/lang/String;)V
    .locals 1
    iget-object p0, p0, Lcom/android/settingslib/core/AbstractPreferenceController;->mContext:Landroid/content/Context;
    const/4 v0, 0x0
    invoke-static {p0, p1, v0}, Landroid/widget/Toast;->makeText(Landroid/content/Context;Ljava/lang/CharSequence;I)Landroid/widget/Toast;
    move-result-object p0
    invoke-virtual {p0}, Landroid/widget/Toast;->show()V
    return-void
.end method

.method private backup()V
    .locals 5
    :try_start_0
    new-instance v0, Ljava/util/Properties;
    invoke-direct {v0}, Ljava/util/Properties;-><init>()V
    iget-object v1, p0, Lcom/android/settingslib/core/AbstractPreferenceController;->mContext:Landroid/content/Context;
    invoke-virtual {v1}, Landroid/content/Context;->getContentResolver()Landroid/content/ContentResolver;
    move-result-object v1
    const-string v2, "unica_allow_downgrade"
    invoke-static {v0, v1, v2}, Lio/mesalabs/unica/settings/BackupRestorePreferenceController;->saveSystem(Ljava/util/Properties;Landroid/content/ContentResolver;Ljava/lang/String;)V
    const-string v2, "unica_allow_sdkbypass"
    invoke-static {v0, v1, v2}, Lio/mesalabs/unica/settings/BackupRestorePreferenceController;->saveSystem(Ljava/util/Properties;Landroid/content/ContentResolver;Ljava/lang/String;)V
    const-string v2, "unica_secure_ss"
    invoke-static {v0, v1, v2}, Lio/mesalabs/unica/settings/BackupRestorePreferenceController;->saveSystem(Ljava/util/Properties;Landroid/content/ContentResolver;Ljava/lang/String;)V
    const-string v2, "unica_ss_detection"
    invoke-static {v0, v1, v2}, Lio/mesalabs/unica/settings/BackupRestorePreferenceController;->saveSystem(Ljava/util/Properties;Landroid/content/ContentResolver;Ljava/lang/String;)V
    const-string v2, "onerom_show_imei"
    invoke-static {v0, v1, v2}, Lio/mesalabs/unica/settings/BackupRestorePreferenceController;->saveSystem(Ljava/util/Properties;Landroid/content/ContentResolver;Ljava/lang/String;)V
    const-string v2, "onerom_show_serial"
    invoke-static {v0, v1, v2}, Lio/mesalabs/unica/settings/BackupRestorePreferenceController;->saveSystem(Ljava/util/Properties;Landroid/content/ContentResolver;Ljava/lang/String;)V
    const-string v2, "onerom_bixby_single_action"
    invoke-static {v0, v1, v2}, Lio/mesalabs/unica/settings/BackupRestorePreferenceController;->saveSystem(Ljava/util/Properties;Landroid/content/ContentResolver;Ljava/lang/String;)V
    const-string v2, "onerom_bixby_double_action"
    invoke-static {v0, v1, v2}, Lio/mesalabs/unica/settings/BackupRestorePreferenceController;->saveSystem(Ljava/util/Properties;Landroid/content/ContentResolver;Ljava/lang/String;)V
    const-string v2, "onerom_bixby_hold_action"
    invoke-static {v0, v1, v2}, Lio/mesalabs/unica/settings/BackupRestorePreferenceController;->saveSystem(Ljava/util/Properties;Landroid/content/ContentResolver;Ljava/lang/String;)V
    const-string v2, "unica_hma"
    invoke-static {v0, v1, v2}, Lio/mesalabs/unica/settings/BackupRestorePreferenceController;->saveSystem(Ljava/util/Properties;Landroid/content/ContentResolver;Ljava/lang/String;)V
    const-string v2, "onerom_show_developer_options"
    invoke-static {v0, v1, v2}, Lio/mesalabs/unica/settings/BackupRestorePreferenceController;->saveSystem(Ljava/util/Properties;Landroid/content/ContentResolver;Ljava/lang/String;)V
    const-string v2, "onerom_show_phone_number"
    invoke-static {v0, v1, v2}, Lio/mesalabs/unica/settings/BackupRestorePreferenceController;->saveSystem(Ljava/util/Properties;Landroid/content/ContentResolver;Ljava/lang/String;)V
    const-string v2, "unica_gphotos"
    invoke-static {v0, v1, v2}, Lio/mesalabs/unica/settings/BackupRestorePreferenceController;->saveSystem(Ljava/util/Properties;Landroid/content/ContentResolver;Ljava/lang/String;)V
    const-string v2, "unica_games_spoof"
    invoke-static {v0, v1, v2}, Lio/mesalabs/unica/settings/BackupRestorePreferenceController;->saveSystem(Ljava/util/Properties;Landroid/content/ContentResolver;Ljava/lang/String;)V
    const-string v2, "unica_asks"
    invoke-static {v0, v1, v2}, Lio/mesalabs/unica/settings/BackupRestorePreferenceController;->saveSystem(Ljava/util/Properties;Landroid/content/ContentResolver;Ljava/lang/String;)V

    const-string v2, "min_refresh_rate"
    invoke-static {v0, v1, v2}, Lio/mesalabs/unica/settings/BackupRestorePreferenceController;->saveSystem(Ljava/util/Properties;Landroid/content/ContentResolver;Ljava/lang/String;)V
    const-string v2, "custom_oneui_banner"
    invoke-static {v1, v2}, Landroid/provider/Settings$Global;->getString(Landroid/content/ContentResolver;Ljava/lang/String;)Ljava/lang/String;
    move-result-object v3
    if-eqz v3, :skip_banner
    invoke-virtual {v0, v2, v3}, Ljava/util/Properties;->setProperty(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/Object;
    :skip_banner
    const-string v2, "development_settings_enabled"
    invoke-static {v1, v2}, Landroid/provider/Settings$Global;->getString(Landroid/content/ContentResolver;Ljava/lang/String;)Ljava/lang/String;
    move-result-object v3
    if-eqz v3, :skip_dev
    invoke-virtual {v0, v2, v3}, Ljava/util/Properties;->setProperty(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/Object;
    :skip_dev
    const-string v2, "persist.sys.unica.bootsound"
    invoke-static {v2}, Landroid/os/SemSystemProperties;->get(Ljava/lang/String;)Ljava/lang/String;
    move-result-object v3
    invoke-virtual {v0, v2, v3}, Ljava/util/Properties;->setProperty(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/Object;
    new-instance v1, Ljava/io/FileOutputStream;
    invoke-direct {p0}, Lio/mesalabs/unica/settings/BackupRestorePreferenceController;->getBackupFile()Ljava/io/File;
    move-result-object v2
    invoke-direct {v1, v2}, Ljava/io/FileOutputStream;-><init>(Ljava/io/File;)V
    const-string v2, "OneROM 9.0 settings"
    invoke-virtual {v0, v1, v2}, Ljava/util/Properties;->store(Ljava/io/OutputStream;Ljava/lang/String;)V
    invoke-virtual {v1}, Ljava/io/FileOutputStream;->close()V
    const-string v0, "Settings backed up to Internal storage/OneROM"
    invoke-direct {p0, v0}, Lio/mesalabs/unica/settings/BackupRestorePreferenceController;->showToast(Ljava/lang/String;)V
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :failed
    return-void
    :failed
    move-exception v0
    const-string v0, "Could not back up OneROM settings"
    invoke-direct {p0, v0}, Lio/mesalabs/unica/settings/BackupRestorePreferenceController;->showToast(Ljava/lang/String;)V
    return-void
.end method

.method private restore()V
    .locals 5
    :try_start_0
    invoke-direct {p0}, Lio/mesalabs/unica/settings/BackupRestorePreferenceController;->getBackupFile()Ljava/io/File;
    move-result-object v0
    invoke-virtual {v0}, Ljava/io/File;->isFile()Z
    move-result v1
    if-nez v1, :load
    const-string v0, "No OneROM settings backup found"
    invoke-direct {p0, v0}, Lio/mesalabs/unica/settings/BackupRestorePreferenceController;->showToast(Ljava/lang/String;)V
    return-void
    :load
    new-instance v1, Ljava/util/Properties;
    invoke-direct {v1}, Ljava/util/Properties;-><init>()V
    new-instance v2, Ljava/io/FileInputStream;
    invoke-direct {v2, v0}, Ljava/io/FileInputStream;-><init>(Ljava/io/File;)V
    invoke-virtual {v1, v2}, Ljava/util/Properties;->load(Ljava/io/InputStream;)V
    invoke-virtual {v2}, Ljava/io/FileInputStream;->close()V
    iget-object v0, p0, Lcom/android/settingslib/core/AbstractPreferenceController;->mContext:Landroid/content/Context;
    invoke-virtual {v0}, Landroid/content/Context;->getContentResolver()Landroid/content/ContentResolver;
    move-result-object v2
    const-string v3, "unica_allow_downgrade"
    invoke-static {v1, v2, v3}, Lio/mesalabs/unica/settings/BackupRestorePreferenceController;->restoreSystem(Ljava/util/Properties;Landroid/content/ContentResolver;Ljava/lang/String;)V
    const-string v3, "unica_allow_sdkbypass"
    invoke-static {v1, v2, v3}, Lio/mesalabs/unica/settings/BackupRestorePreferenceController;->restoreSystem(Ljava/util/Properties;Landroid/content/ContentResolver;Ljava/lang/String;)V
    const-string v3, "unica_secure_ss"
    invoke-static {v1, v2, v3}, Lio/mesalabs/unica/settings/BackupRestorePreferenceController;->restoreSystem(Ljava/util/Properties;Landroid/content/ContentResolver;Ljava/lang/String;)V
    const-string v3, "unica_ss_detection"
    invoke-static {v1, v2, v3}, Lio/mesalabs/unica/settings/BackupRestorePreferenceController;->restoreSystem(Ljava/util/Properties;Landroid/content/ContentResolver;Ljava/lang/String;)V
    const-string v3, "onerom_show_imei"
    invoke-static {v1, v2, v3}, Lio/mesalabs/unica/settings/BackupRestorePreferenceController;->restoreSystem(Ljava/util/Properties;Landroid/content/ContentResolver;Ljava/lang/String;)V
    const-string v3, "onerom_show_serial"
    invoke-static {v1, v2, v3}, Lio/mesalabs/unica/settings/BackupRestorePreferenceController;->restoreSystem(Ljava/util/Properties;Landroid/content/ContentResolver;Ljava/lang/String;)V
    const-string v3, "onerom_bixby_single_action"
    invoke-static {v1, v2, v3}, Lio/mesalabs/unica/settings/BackupRestorePreferenceController;->restoreSystem(Ljava/util/Properties;Landroid/content/ContentResolver;Ljava/lang/String;)V
    const-string v3, "onerom_bixby_double_action"
    invoke-static {v1, v2, v3}, Lio/mesalabs/unica/settings/BackupRestorePreferenceController;->restoreSystem(Ljava/util/Properties;Landroid/content/ContentResolver;Ljava/lang/String;)V
    const-string v3, "onerom_bixby_hold_action"
    invoke-static {v1, v2, v3}, Lio/mesalabs/unica/settings/BackupRestorePreferenceController;->restoreSystem(Ljava/util/Properties;Landroid/content/ContentResolver;Ljava/lang/String;)V
    const-string v3, "unica_hma"
    invoke-static {v1, v2, v3}, Lio/mesalabs/unica/settings/BackupRestorePreferenceController;->restoreSystem(Ljava/util/Properties;Landroid/content/ContentResolver;Ljava/lang/String;)V
    const-string v3, "onerom_show_developer_options"
    invoke-static {v1, v2, v3}, Lio/mesalabs/unica/settings/BackupRestorePreferenceController;->restoreSystem(Ljava/util/Properties;Landroid/content/ContentResolver;Ljava/lang/String;)V
    const-string v3, "onerom_show_phone_number"
    invoke-static {v1, v2, v3}, Lio/mesalabs/unica/settings/BackupRestorePreferenceController;->restoreSystem(Ljava/util/Properties;Landroid/content/ContentResolver;Ljava/lang/String;)V
    const-string v3, "unica_gphotos"
    invoke-static {v1, v2, v3}, Lio/mesalabs/unica/settings/BackupRestorePreferenceController;->restoreSystem(Ljava/util/Properties;Landroid/content/ContentResolver;Ljava/lang/String;)V
    const-string v3, "unica_games_spoof"
    invoke-static {v1, v2, v3}, Lio/mesalabs/unica/settings/BackupRestorePreferenceController;->restoreSystem(Ljava/util/Properties;Landroid/content/ContentResolver;Ljava/lang/String;)V
    const-string v3, "unica_asks"
    invoke-static {v1, v2, v3}, Lio/mesalabs/unica/settings/BackupRestorePreferenceController;->restoreSystem(Ljava/util/Properties;Landroid/content/ContentResolver;Ljava/lang/String;)V

    const-string v3, "min_refresh_rate"
    invoke-static {v1, v2, v3}, Lio/mesalabs/unica/settings/BackupRestorePreferenceController;->restoreSystem(Ljava/util/Properties;Landroid/content/ContentResolver;Ljava/lang/String;)V
    const-string v3, "custom_oneui_banner"
    invoke-virtual {v1, v3}, Ljava/util/Properties;->getProperty(Ljava/lang/String;)Ljava/lang/String;
    move-result-object v4
    if-eqz v4, :skip_banner
    invoke-static {v2, v3, v4}, Landroid/provider/Settings$Global;->putString(Landroid/content/ContentResolver;Ljava/lang/String;Ljava/lang/String;)Z
    :skip_banner
    const-string v3, "development_settings_enabled"
    invoke-virtual {v1, v3}, Ljava/util/Properties;->getProperty(Ljava/lang/String;)Ljava/lang/String;
    move-result-object v4
    if-eqz v4, :skip_dev
    invoke-static {v4}, Ljava/lang/Integer;->parseInt(Ljava/lang/String;)I
    move-result v4
    if-eqz v4, :dev_off
    const/4 v4, 0x1
    goto :set_dev
    :dev_off
    const/4 v4, 0x0
    :set_dev
    invoke-static {v0, v4}, Lcom/android/settingslib/development/DevelopmentSettingsEnabler;->setDevelopmentSettingsEnabled(Landroid/content/Context;Z)V
    :skip_dev
    const-string v3, "persist.sys.unica.bootsound"
    invoke-virtual {v1, v3}, Ljava/util/Properties;->getProperty(Ljava/lang/String;)Ljava/lang/String;
    move-result-object v4
    if-eqz v4, :done
    invoke-static {v3, v4}, Landroid/os/SemSystemProperties;->set(Ljava/lang/String;Ljava/lang/String;)V
    :done
    const-string v0, "OneROM settings restored"
    invoke-direct {p0, v0}, Lio/mesalabs/unica/settings/BackupRestorePreferenceController;->showToast(Ljava/lang/String;)V
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :failed
    return-void
    :failed
    move-exception v0
    const-string v0, "Could not restore OneROM settings"
    invoke-direct {p0, v0}, Lio/mesalabs/unica/settings/BackupRestorePreferenceController;->showToast(Ljava/lang/String;)V
    return-void
.end method

.method public getAvailabilityStatus()I
    .locals 1
    const/4 v0, 0x0
    return v0
.end method

.method public handlePreferenceTreeClick(Landroidx/preference/Preference;)Z
    .locals 2
    invoke-virtual {p1}, Landroidx/preference/Preference;->getKey()Ljava/lang/String;
    move-result-object p1
    invoke-virtual {p0}, Lcom/android/settings/core/BasePreferenceController;->getPreferenceKey()Ljava/lang/String;
    move-result-object v0
    invoke-virtual {v0, p1}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v1
    if-nez v1, :matched
    const/4 v0, 0x0
    return v0
    :matched
    const-string v1, "onerom_backup_settings"
    invoke-virtual {v1, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v0
    if-eqz v0, :restore
    invoke-direct {p0}, Lio/mesalabs/unica/settings/BackupRestorePreferenceController;->backup()V
    goto :done
    :restore
    invoke-direct {p0}, Lio/mesalabs/unica/settings/BackupRestorePreferenceController;->restore()V
    :done
    const/4 v0, 0x1
    return v0
.end method