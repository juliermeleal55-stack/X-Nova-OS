.class Lio/mesalabs/unica/settings/DoubleTapAboutPreferenceController$1;
.super Ljava/lang/Object;
.source "DoubleTapAboutPreferenceController.java"

.implements Ljava/lang/Runnable;

.field final synthetic this$0:Lio/mesalabs/unica/settings/DoubleTapAboutPreferenceController;

.method constructor <init>(Lio/mesalabs/unica/settings/DoubleTapAboutPreferenceController;)V
    .locals 0
    iput-object p1, p0, Lio/mesalabs/unica/settings/DoubleTapAboutPreferenceController$1;->this$0:Lio/mesalabs/unica/settings/DoubleTapAboutPreferenceController;
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    return-void
.end method

.method public run()V
    .locals 2
    iget-object v0, p0, Lio/mesalabs/unica/settings/DoubleTapAboutPreferenceController$1;->this$0:Lio/mesalabs/unica/settings/DoubleTapAboutPreferenceController;
    const/4 v1, 0x0
    iput-boolean v1, v0, Lio/mesalabs/unica/settings/DoubleTapAboutPreferenceController;->mPending:Z
    const-string v1, "com.samsung.android.settings.deviceinfo.aboutphone.SecMyDeviceInfoFragment"
    invoke-virtual {v0, v1}, Lio/mesalabs/unica/settings/DoubleTapAboutPreferenceController;->launchDestination(Ljava/lang/String;)V
    return-void
.end method