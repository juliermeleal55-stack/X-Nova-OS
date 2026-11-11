.class public Lio/mesalabs/unica/settings/extra/BixbyKeyActionPreferenceController;
.super Lcom/android/settings/core/BasePreferenceController;
.source "BixbyKeyActionPreferenceController.java"

# interfaces
.implements Landroidx/preference/Preference$OnPreferenceChangeListener;


# instance fields
.field private mPreference:Landroidx/preference/SecDropDownPreference;


# direct methods
.method public constructor <init>(Landroid/content/Context;Ljava/lang/String;)V
    .registers 3

    invoke-direct {p0, p1, p2}, Lcom/android/settings/core/BasePreferenceController;-><init>(Landroid/content/Context;Ljava/lang/String;)V

    return-void
.end method

.method private applyAction(Ljava/lang/String;I)V
    .registers 11

    iget-object v0, p0, Lcom/android/settingslib/core/AbstractPreferenceController;->mContext:Landroid/content/Context;

    invoke-virtual {v0}, Landroid/content/Context;->getContentResolver()Landroid/content/ContentResolver;

    move-result-object v0

    const-string/jumbo v1, "xcover_top_key_on_lockscreen"

    const/4 v2, 0x1

    invoke-static {v0, v1, v2}, Landroid/provider/Settings$System;->putInt(Landroid/content/ContentResolver;Ljava/lang/String;I)Z

    new-instance v5, Landroid/content/Intent;

    invoke-direct {v5}, Landroid/content/Intent;-><init>()V

    const-string v0, "com.android.settings"

    const-string v1, "io.mesalabs.unica.BixbyKeyActionActivity"

    invoke-virtual {v5, v0, v1}, Landroid/content/Intent;->setClassName(Ljava/lang/String;Ljava/lang/String;)Landroid/content/Intent;

    const-string v0, "onerom_action"

    invoke-virtual {v5, v0, p1}, Landroid/content/Intent;->putExtra(Ljava/lang/String;Ljava/lang/String;)Landroid/content/Intent;

    const v0, 0x10810000

    invoke-virtual {v5, v0}, Landroid/content/Intent;->addFlags(I)Landroid/content/Intent;

    :try_start_24
    invoke-static {}, Landroid/view/WindowManagerGlobal;->getWindowManagerService()Landroid/view/IWindowManager;

    move-result-object v6

    const/16 v0, 0x44f

    const/16 v1, 0x3f7

    invoke-interface {v6, v0, p2, v1}, Landroid/view/IWindowManager;->removeKeyCustomizationInfo(III)V

    new-instance v0, Lcom/samsung/android/view/SemWindowManager$KeyCustomizationInfo;

    move v1, p2

    const/16 v2, 0x7d3

    const/16 v3, 0x3f7

    const/4 v4, 0x1

    invoke-direct/range {v0 .. v5}, Lcom/samsung/android/view/SemWindowManager$KeyCustomizationInfo;-><init>(IIIILandroid/content/Intent;)V

    const-string v1, "com.android.settings"

    iput-object v1, v0, Lcom/samsung/android/view/SemWindowManager$KeyCustomizationInfo;->ownerPackage:Ljava/lang/String;

    invoke-interface {v6, v0}, Landroid/view/IWindowManager;->putKeyCustomizationInfo(Lcom/samsung/android/view/SemWindowManager$KeyCustomizationInfo;)V
    :try_end_41
    .catch Ljava/lang/Exception; {:try_start_24 .. :try_end_41} :catch_42

    return-void

    :catch_42
    move-exception v0

    const-string v1, "OneROMBixbyKey"

    const-string v2, "Unable to register key customization"

    invoke-static {v1, v2, v0}, Landroid/util/Log;->e(Ljava/lang/String;Ljava/lang/String;Ljava/lang/Throwable;)I

    return-void
.end method


# virtual methods
.method public displayPreference(Landroidx/preference/PreferenceScreen;)V
    .registers 12

    invoke-super {p0, p1}, Lcom/android/settings/core/BasePreferenceController;->displayPreference(Landroidx/preference/PreferenceScreen;)V

    :try_start_3
    invoke-virtual {p0}, Lcom/android/settings/core/BasePreferenceController;->getPreferenceKey()Ljava/lang/String;

    move-result-object v0

    invoke-virtual {p1, v0}, Landroidx/preference/PreferenceGroup;->findPreference(Ljava/lang/CharSequence;)Landroidx/preference/Preference;

    move-result-object v0

    if-nez v0, :cond_e

    return-void

    :cond_e
    check-cast v0, Landroidx/preference/SecDropDownPreference;

    iput-object v0, p0, Lio/mesalabs/unica/settings/extra/BixbyKeyActionPreferenceController;->mPreference:Landroidx/preference/SecDropDownPreference;

    const/4 v1, 0x6

    new-array v2, v1, [Ljava/lang/CharSequence;

    const-string v3, "Voice assistant"

    const/4 v4, 0x0

    aput-object v3, v2, v4

    const-string v3, "Camera"

    const/4 v5, 0x1

    aput-object v3, v2, v5

    const-string v3, "Flashlight"

    const/4 v6, 0x2

    aput-object v3, v2, v6

    const-string v3, "No action"

    const/4 v7, 0x3

    aput-object v3, v2, v7

    const-string v3, "Screenshot"

    const/4 v8, 0x4

    aput-object v3, v2, v8

    const-string v3, "Play/Pause"

    const/4 v9, 0x5

    aput-object v3, v2, v9

    invoke-virtual {v0, v2}, Landroidx/preference/DropDownPreference;->setEntries([Ljava/lang/CharSequence;)V

    new-array v2, v1, [Ljava/lang/CharSequence;

    const-string v3, "voice"

    aput-object v3, v2, v4

    const-string v3, "camera"

    aput-object v3, v2, v5

    const-string v3, "torch"

    aput-object v3, v2, v6

    const-string v3, "none"

    aput-object v3, v2, v7

    const-string v3, "screenshot"

    aput-object v3, v2, v8

    const-string v3, "media"

    aput-object v3, v2, v9

    iput-object v2, v0, Landroidx/preference/ListPreference;->mEntryValues:[Ljava/lang/CharSequence;

    iget-object v1, p0, Lcom/android/settingslib/core/AbstractPreferenceController;->mContext:Landroid/content/Context;

    invoke-virtual {v1}, Landroid/content/Context;->getContentResolver()Landroid/content/ContentResolver;

    move-result-object v1

    invoke-virtual {p0}, Lcom/android/settings/core/BasePreferenceController;->getPreferenceKey()Ljava/lang/String;

    move-result-object v2

    invoke-static {v1, v2}, Landroid/provider/Settings$System;->getString(Landroid/content/ContentResolver;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v1

    if-nez v1, :cond_64

    const-string v1, "voice"

    :cond_64
    const-string v2, "camera"

    invoke-virtual {v2, v1}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v2

    if-eqz v2, :cond_6e

    move v4, v5

    goto :goto_95

    :cond_6e
    const-string v2, "torch"

    invoke-virtual {v2, v1}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v2

    if-eqz v2, :cond_78

    move v4, v6

    goto :goto_95

    :cond_78
    const-string v2, "screenshot"

    invoke-virtual {v2, v1}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v2

    if-eqz v2, :cond_82

    move v4, v8

    goto :goto_95

    :cond_82
    const-string v2, "media"

    invoke-virtual {v2, v1}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v2

    if-eqz v2, :cond_8c

    move v4, v9

    goto :goto_95

    :cond_8c
    const-string v2, "none"

    invoke-virtual {v2, v1}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v2

    if-eqz v2, :cond_95

    move v4, v7

    :cond_95
    :goto_95
    invoke-virtual {v0, v4}, Landroidx/preference/DropDownPreference;->setValueIndex(I)V

    invoke-virtual {v0, p0}, Landroidx/preference/DropDownPreference;->setOnPreferenceChangeListener(Landroidx/preference/Preference$OnPreferenceChangeListener;)V

    const/4 v2, 0x3

    invoke-virtual {p0}, Lcom/android/settings/core/BasePreferenceController;->getPreferenceKey()Ljava/lang/String;

    move-result-object v3

    const-string v4, "onerom_bixby_double_action"

    invoke-virtual {v4, v3}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v4

    if-eqz v4, :cond_ab

    const/16 v2, 0x8

    goto :goto_b4

    :cond_ab
    const-string v4, "onerom_bixby_hold_action"

    invoke-virtual {v4, v3}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v3

    if-eqz v3, :cond_b4

    const/4 v2, 0x4

    :cond_b4
    :goto_b4
    invoke-direct {p0, v1, v2}, Lio/mesalabs/unica/settings/extra/BixbyKeyActionPreferenceController;->applyAction(Ljava/lang/String;I)V
    :try_end_b7
    .catch Ljava/lang/Throwable; {:try_start_3 .. :try_end_b7} :catch_b8

    return-void

    :catch_b8
    move-exception v0

    const-string v1, "OneROMBixbyKey"

    const-string v2, "Failed to display Bixby preference"

    invoke-static {v1, v2, v0}, Landroid/util/Log;->e(Ljava/lang/String;Ljava/lang/String;Ljava/lang/Throwable;)I

    return-void
.end method

.method public getAvailabilityStatus()I
    .registers 2

    const/4 v0, 0x0

    return v0
.end method

.method public onPreferenceChange(Landroidx/preference/Preference;Ljava/lang/Object;)Z
    .registers 6

    check-cast p2, Ljava/lang/String;

    iget-object v0, p0, Lcom/android/settingslib/core/AbstractPreferenceController;->mContext:Landroid/content/Context;

    invoke-virtual {v0}, Landroid/content/Context;->getContentResolver()Landroid/content/ContentResolver;

    move-result-object v0

    invoke-virtual {p0}, Lcom/android/settings/core/BasePreferenceController;->getPreferenceKey()Ljava/lang/String;

    move-result-object v1

    invoke-static {v0, v1, p2}, Landroid/provider/Settings$System;->putString(Landroid/content/ContentResolver;Ljava/lang/String;Ljava/lang/String;)Z

    const/4 v2, 0x3

    const-string v0, "onerom_bixby_double_action"

    invoke-virtual {v0, v1}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-eqz v0, :cond_1b

    const/16 v2, 0x8

    goto :goto_24

    :cond_1b
    const-string v0, "onerom_bixby_hold_action"

    invoke-virtual {v0, v1}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-eqz v0, :cond_24

    const/4 v2, 0x4

    :cond_24
    :goto_24
    invoke-direct {p0, p2, v2}, Lio/mesalabs/unica/settings/extra/BixbyKeyActionPreferenceController;->applyAction(Ljava/lang/String;I)V

    const/4 v0, 0x1

    return v0
.end method
