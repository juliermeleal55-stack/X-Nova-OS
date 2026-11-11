.class public Lio/mesalabs/unica/settings/UnicaSettingsFragment;
.super Lcom/android/settings/dashboard/DashboardFragment;

.method public constructor <init>()V
    .locals 0
    invoke-direct {p0}, Lcom/android/settings/dashboard/DashboardFragment;-><init>()V
    return-void
.end method

.method public getMetricsCategory()I
    .locals 1
    const/16 v0, 0x2e8
    return v0
.end method

.method public getLogTag()Ljava/lang/String;
    .locals 1
    const-string v0, "OneROMSettings"
    return-object v0
.end method

.method public getPreferenceScreenResId()I
    .locals 4
    invoke-virtual {p0}, Landroidx/fragment/app/Fragment;->getContext()Landroid/content/Context;
    move-result-object v0
    invoke-virtual {v0}, Landroid/content/Context;->getResources()Landroid/content/res/Resources;
    move-result-object v1
    invoke-virtual {v0}, Landroid/content/Context;->getPackageName()Ljava/lang/String;
    move-result-object v0
    const-string v2, "unica_top_settings"
    const-string v3, "xml"
    invoke-virtual {v1, v2, v3, v0}, Landroid/content/res/Resources;->getIdentifier(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)I
    move-result v0
    return v0
.end method