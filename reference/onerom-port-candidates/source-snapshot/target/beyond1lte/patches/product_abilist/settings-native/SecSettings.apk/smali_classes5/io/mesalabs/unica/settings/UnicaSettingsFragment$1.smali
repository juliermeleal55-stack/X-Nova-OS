.class public final Lio/mesalabs/unica/settings/UnicaSettingsFragment$1;
.super Ljava/lang/Object;
.source "UnicaSettingsFragment.java"

# interfaces
.implements Landroidx/appcompat/widget/PopupMenu$OnMenuItemClickListener;


# instance fields
.field public final synthetic this$0:Lio/mesalabs/unica/settings/UnicaSettingsFragment;


# direct methods
.method public constructor <init>(Lio/mesalabs/unica/settings/UnicaSettingsFragment;)V
    .locals 0

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    iput-object p1, p0, Lio/mesalabs/unica/settings/UnicaSettingsFragment$1;->this$0:Lio/mesalabs/unica/settings/UnicaSettingsFragment;

    return-void
.end method


# virtual methods
.method public final onMenuItemClick(Landroid/view/MenuItem;)Z
    .locals 4

    :try_start_0
    iget-object v0, p0, Lio/mesalabs/unica/settings/UnicaSettingsFragment$1;->this$0:Lio/mesalabs/unica/settings/UnicaSettingsFragment;

    invoke-virtual {v0}, Landroidx/fragment/app/Fragment;->getContext()Landroid/content/Context;

    move-result-object v0

    if-nez v0, :cond_ctx_ok

    const/4 v0, 0x1

    return v0

    :cond_ctx_ok
    const-string v1, "power"

    invoke-virtual {v0, v1}, Landroid/content/Context;->getSystemService(Ljava/lang/String;)Ljava/lang/Object;

    move-result-object v0

    check-cast v0, Landroid/os/PowerManager;

    if-nez v0, :cond_pm_ok

    const/4 v0, 0x1

    return v0

    :cond_pm_ok
    invoke-interface {p1}, Landroid/view/MenuItem;->getItemId()I

    move-result v1

    const/4 v2, 0x1

    if-eq v1, v2, :cond_2

    const/4 v3, 0x2

    if-eq v1, v3, :cond_1

    const/4 v3, 0x3

    if-eq v1, v3, :cond_0

    const/4 v1, 0x0

    goto :goto_0

    :cond_0
    const-string v1, "download"

    goto :goto_0

    :cond_1
    const-string v1, "fastboot"

    goto :goto_0

    :cond_2
    const-string v1, "recovery"

    :goto_0
    invoke-virtual {v0, v1}, Landroid/os/PowerManager;->reboot(Ljava/lang/String;)V
    :try_end_0
    .catch Ljava/lang/Throwable; {:try_start_0 .. :try_end_0} :catch_0

    goto :goto_1

    :catch_0
    move-exception v0

    const-string v1, "UnicaSettingsFragment"

    const-string v2, "Failed to reboot from menu"

    invoke-static {v1, v2, v0}, Landroid/util/Log;->e(Ljava/lang/String;Ljava/lang/String;Ljava/lang/Throwable;)I

    :goto_1
    const/4 v0, 0x1

    return v0
.end method
