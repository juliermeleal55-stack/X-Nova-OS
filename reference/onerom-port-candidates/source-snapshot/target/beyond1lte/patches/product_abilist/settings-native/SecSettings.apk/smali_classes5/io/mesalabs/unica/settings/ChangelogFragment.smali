.class public Lio/mesalabs/unica/settings/ChangelogFragment;
.super Lcom/android/settings/dashboard/DashboardFragment;
.source "ChangelogFragment.java"


# direct methods
.method public constructor <init>()V
    .registers 1

    invoke-direct {p0}, Lcom/android/settings/dashboard/DashboardFragment;-><init>()V

    return-void
.end method


# virtual methods
.method public final getLogTag()Ljava/lang/String;
    .registers 2

    const-string v0, "OneROMChangelog"

    return-object v0
.end method

.method public final getMetricsCategory()I
    .registers 2

    const/16 v0, 0x2e8

    return v0
.end method

.method public final getPreferenceScreenResId()I
    .registers 2

    const/4 v0, 0x0

    return v0
.end method

.method public onCreatePreferences(Landroid/os/Bundle;Ljava/lang/String;)V
    .registers 8

    invoke-virtual {p0}, Landroidx/preference/PreferenceFragmentCompat;->getPreferenceManager()Landroidx/preference/PreferenceManager;

    move-result-object p1

    invoke-virtual {p0}, Landroidx/fragment/app/Fragment;->getContext()Landroid/content/Context;

    move-result-object p2

    invoke-virtual {p1, p2}, Landroidx/preference/PreferenceManager;->createPreferenceScreen(Landroid/content/Context;)Landroidx/preference/PreferenceScreen;

    move-result-object p1

    new-instance v0, Landroidx/preference/PreferenceCategory;

    invoke-direct {v0, p2}, Landroidx/preference/PreferenceCategory;-><init>(Landroid/content/Context;)V

    const-string v1, "OneROM Delta 9.0"

    invoke-virtual {v0, v1}, Landroidx/preference/Preference;->setTitle(Ljava/lang/CharSequence;)V

    invoke-virtual {p1, v0}, Landroidx/preference/PreferenceGroup;->addPreference(Landroidx/preference/Preference;)Z

    const/4 v2, 0x0

    new-instance v1, Landroidx/preference/Preference;

    invoke-direct {v1, p2}, Landroidx/preference/Preference;-><init>(Landroid/content/Context;)V

    invoke-virtual {v1, v2}, Landroidx/preference/Preference;->setSelectable(Z)V

    const-string v3, "Initial Release"

    invoke-virtual {v1, v3}, Landroidx/preference/Preference;->setTitle(Ljava/lang/CharSequence;)V

    const-string v3, "Initial One UI 9 Android 17 port for Galaxy S10 (beyond1lte)."

    invoke-virtual {v1, v3}, Landroidx/preference/Preference;->setSummary(Ljava/lang/CharSequence;)V

    invoke-virtual {v0, v1}, Landroidx/preference/PreferenceGroup;->addPreference(Landroidx/preference/Preference;)Z

    invoke-virtual {p0, p1}, Landroidx/preference/PreferenceFragmentCompat;->setPreferenceScreen(Landroidx/preference/PreferenceScreen;)V

    return-void
.end method
