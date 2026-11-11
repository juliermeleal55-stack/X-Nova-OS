.class public Lio/mesalabs/unica/settings/CustomBannerPreferenceController;
.super Lcom/android/settings/core/BasePreferenceController;
.source "CustomBannerPreferenceController.java"

# interfaces
.implements Landroidx/preference/Preference$OnPreferenceChangeListener;

.method public constructor <init>(Landroid/content/Context;Ljava/lang/String;)V
    .locals 0
    invoke-direct {p0, p1, p2}, Lcom/android/settings/core/BasePreferenceController;-><init>(Landroid/content/Context;Ljava/lang/String;)V
    return-void
.end method

.method private getBannerText()Ljava/lang/String;
    .locals 2
    iget-object v0, p0, Lcom/android/settingslib/core/AbstractPreferenceController;->mContext:Landroid/content/Context;
    invoke-virtual {v0}, Landroid/content/Context;->getContentResolver()Landroid/content/ContentResolver;
    move-result-object v0
    const-string v1, "custom_oneui_banner"
    invoke-static {v0, v1}, Landroid/provider/Settings$Global;->getString(Landroid/content/ContentResolver;Ljava/lang/String;)Ljava/lang/String;
    move-result-object v0
    invoke-static {v0}, Landroid/text/TextUtils;->isEmpty(Ljava/lang/CharSequence;)Z
    move-result v1
    if-eqz v1, :done
    const-string v0, "OneROM 9.0"
    :done
    return-object v0
.end method

.method public getAvailabilityStatus()I
    .locals 1
    const/4 v0, 0x0
    return v0
.end method

.method public getSummary()Ljava/lang/CharSequence;
    .locals 1
    invoke-direct {p0}, Lio/mesalabs/unica/settings/CustomBannerPreferenceController;->getBannerText()Ljava/lang/String;
    move-result-object v0
    return-object v0
.end method

.method public displayPreference(Landroidx/preference/PreferenceScreen;)V
    .locals 2
    invoke-super {p0, p1}, Lcom/android/settingslib/core/AbstractPreferenceController;->displayPreference(Landroidx/preference/PreferenceScreen;)V
    iget-object v0, p0, Lcom/android/settings/core/BasePreferenceController;->mPreferenceKey:Ljava/lang/String;
    invoke-virtual {p1, v0}, Landroidx/preference/PreferenceGroup;->findPreference(Ljava/lang/CharSequence;)Landroidx/preference/Preference;
    move-result-object p1
    invoke-virtual {p1, p0}, Landroidx/preference/Preference;->setOnPreferenceChangeListener(Landroidx/preference/Preference$OnPreferenceChangeListener;)V
    check-cast p1, Landroidx/preference/EditTextPreference;
    invoke-direct {p0}, Lio/mesalabs/unica/settings/CustomBannerPreferenceController;->getBannerText()Ljava/lang/String;
    move-result-object v0
    invoke-virtual {p1, v0}, Landroidx/preference/EditTextPreference;->setText(Ljava/lang/String;)V
    return-void
.end method

.method public onPreferenceChange(Landroidx/preference/Preference;Ljava/lang/Object;)Z
    .locals 2
    check-cast p2, Ljava/lang/String;
    invoke-virtual {p2}, Ljava/lang/String;->trim()Ljava/lang/String;
    move-result-object p2
    iget-object v0, p0, Lcom/android/settingslib/core/AbstractPreferenceController;->mContext:Landroid/content/Context;
    invoke-virtual {v0}, Landroid/content/Context;->getContentResolver()Landroid/content/ContentResolver;
    move-result-object v0
    const-string v1, "custom_oneui_banner"
    invoke-static {v0, v1, p2}, Landroid/provider/Settings$Global;->putString(Landroid/content/ContentResolver;Ljava/lang/String;Ljava/lang/String;)Z
    invoke-virtual {p1, p2}, Landroidx/preference/Preference;->setSummary(Ljava/lang/CharSequence;)V
    const/4 v0, 0x1
    return v0
.end method