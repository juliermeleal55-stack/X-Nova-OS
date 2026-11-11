.class public Lio/mesalabs/unica/settings/spoof/SpoofSettingsFragment;
.super Lcom/android/settings/dashboard/DashboardFragment;
.source "SpoofSettingsFragment.java"


# static fields
.field public static final SEARCH_INDEX_DATA_PROVIDER:Lcom/android/settings/search/BaseSearchIndexProvider;

.field public static sNeedsAboutPhoneRestart:Z


# direct methods
.method public static constructor <clinit>()V
    .locals 3

    new-instance v0, Lio/mesalabs/unica/settings/spoof/SpoofSettingsFragment$1;

    const-string v1, "xml"

    const-string v2, "unica_spoof_settings"

    invoke-static {v1, v2}, Lio/mesalabs/unica/utils/Utils;->getResourceId(Ljava/lang/String;Ljava/lang/String;)I

    move-result v1

    invoke-direct {v0, v1}, Lcom/android/settings/search/BaseSearchIndexProvider;-><init>(I)V

    sput-object v0, Lio/mesalabs/unica/settings/spoof/SpoofSettingsFragment;->SEARCH_INDEX_DATA_PROVIDER:Lcom/android/settings/search/BaseSearchIndexProvider;

    return-void
.end method

.method public constructor <init>()V
    .locals 0

    invoke-direct {p0}, Lcom/android/settings/dashboard/DashboardFragment;-><init>()V

    return-void
.end method

.method public static buildPreferenceControllers$1(Landroid/content/Context;Landroidx/fragment/app/Fragment;)Ljava/util/List;
    .locals 3

    new-instance v0, Ljava/util/ArrayList;

    invoke-direct {v0}, Ljava/util/ArrayList;-><init>()V

    new-instance v1, Lio/mesalabs/unica/settings/keybox/KeyboxLoadPreferenceController;

    const-string/jumbo v2, "unica_keybox_load"

    invoke-direct {v1, p0, v2, p1}, Lio/mesalabs/unica/settings/keybox/KeyboxLoadPreferenceController;-><init>(Landroid/content/Context;Ljava/lang/String;Landroidx/fragment/app/Fragment;)V

    invoke-virtual {v0, v1}, Ljava/util/ArrayList;->add(Ljava/lang/Object;)Z

    new-instance v1, Lio/mesalabs/unica/settings/pif/PIFCustomPreferenceController;

    const-string/jumbo v2, "unica_pif_custom"

    invoke-direct {v1, p0, v2, p1}, Lio/mesalabs/unica/settings/pif/PIFCustomPreferenceController;-><init>(Landroid/content/Context;Ljava/lang/String;Landroidx/fragment/app/Fragment;)V

    invoke-virtual {v0, v1}, Ljava/util/ArrayList;->add(Ljava/lang/Object;)Z

    return-object v0
.end method


# virtual methods
.method public final createPreferenceControllers(Landroid/content/Context;)Ljava/util/List;
    .locals 0

    invoke-static {p1, p0}, Lio/mesalabs/unica/settings/spoof/SpoofSettingsFragment;->buildPreferenceControllers$1(Landroid/content/Context;Landroidx/fragment/app/Fragment;)Ljava/util/List;

    move-result-object p0

    return-object p0
.end method

.method public final getLogTag()Ljava/lang/String;
    .locals 0

    const-string p0, "SpoofSettingsFragment"

    return-object p0
.end method

.method public final getMetricsCategory()I
    .locals 0

    const/16 p0, 0x2e8

    return p0
.end method

.method public final getPreferenceScreenResId()I
    .locals 1

    const-string p0, "xml"

    const-string v0, "unica_spoof_settings"

    invoke-static {p0, v0}, Lio/mesalabs/unica/utils/Utils;->getResourceId(Ljava/lang/String;Ljava/lang/String;)I

    move-result p0

    return p0
.end method

.method public final onCreate(Landroid/os/Bundle;)V
    .locals 0

    invoke-super {p0, p1}, Lcom/android/settings/dashboard/DashboardFragment;->onCreate(Landroid/os/Bundle;)V

    const/4 p1, 0x1

    invoke-virtual {p0, p1}, Lcom/android/settings/SettingsPreferenceFragment;->setAnimationAllowed(Z)V

    return-void
.end method

.method public onDestroy()V
    .locals 4

    invoke-super {p0}, Lcom/android/settings/dashboard/DashboardFragment;->onDestroy()V

    sget-boolean v0, Lio/mesalabs/unica/settings/spoof/SpoofSettingsFragment;->sNeedsAboutPhoneRestart:Z

    if-eqz v0, :not_needed

    const/4 v0, 0x0

    sput-boolean v0, Lio/mesalabs/unica/settings/spoof/SpoofSettingsFragment;->sNeedsAboutPhoneRestart:Z

    invoke-virtual {p0}, Landroidx/fragment/app/Fragment;->getActivity()Landroidx/fragment/app/FragmentActivity;

    move-result-object v0

    if-eqz v0, :not_needed

    new-instance v1, Landroid/content/Intent;

    const-string v2, "android.intent.action.MAIN"

    invoke-direct {v1, v2}, Landroid/content/Intent;-><init>(Ljava/lang/String;)V

    new-instance v2, Landroid/content/ComponentName;

    const-string v3, "com.android.settings"

    const-string p0, "com.android.settings.Settings$MyDeviceInfoActivity"

    invoke-direct {v2, v3, p0}, Landroid/content/ComponentName;-><init>(Ljava/lang/String;Ljava/lang/String;)V

    invoke-virtual {v1, v2}, Landroid/content/Intent;->setComponent(Landroid/content/ComponentName;)Landroid/content/Intent;

    const p0, 0x10008000

    invoke-virtual {v1, p0}, Landroid/content/Intent;->addFlags(I)Landroid/content/Intent;

    invoke-virtual {v0, v1}, Landroid/content/Context;->startActivity(Landroid/content/Intent;)V

    :not_needed
    return-void
.end method
