.class public Lio/mesalabs/unica/BixbyKeyActionActivity;
.super Landroid/app/Activity;
.source "BixbyKeyActionActivity.java"


# static fields
.field public static final EXTRA_ACTION:Ljava/lang/String; = "onerom_action"

.field private static final TAG:Ljava/lang/String; = "OneROMBixbyKey"


# direct methods
.method public constructor <init>()V
    .registers 1

    .line 20
    invoke-direct {p0}, Landroid/app/Activity;-><init>()V

    return-void
.end method

.method private static dispatchMediaKey(Landroid/content/Context;)V
    .registers 9

    .line 96
    const-class v0, Landroid/media/AudioManager;

    invoke-virtual {p0, v0}, Landroid/content/Context;->getSystemService(Ljava/lang/Class;)Ljava/lang/Object;

    move-result-object p0

    check-cast p0, Landroid/media/AudioManager;

    .line 97
    invoke-static {}, Landroid/os/SystemClock;->uptimeMillis()J

    move-result-wide v1

    .line 98
    new-instance v0, Landroid/view/KeyEvent;

    const/16 v6, 0x55

    const/4 v7, 0x0

    const/4 v5, 0x0

    move-wide v3, v1

    invoke-direct/range {v0 .. v7}, Landroid/view/KeyEvent;-><init>(JJIII)V

    invoke-virtual {p0, v0}, Landroid/media/AudioManager;->dispatchMediaKeyEvent(Landroid/view/KeyEvent;)V

    .line 99
    new-instance v0, Landroid/view/KeyEvent;

    const/4 v5, 0x1

    invoke-direct/range {v0 .. v7}, Landroid/view/KeyEvent;-><init>(JJIII)V

    invoke-virtual {p0, v0}, Landroid/media/AudioManager;->dispatchMediaKeyEvent(Landroid/view/KeyEvent;)V

    .line 100
    return-void
.end method

.method private static injectKeyLater(IJ)V
    .registers 5

    .line 104
    new-instance v0, Ljava/lang/Thread;

    new-instance v1, Lio/mesalabs/unica/BixbyKeyActionActivity$$ExternalSyntheticLambda0;

    invoke-direct {v1, p1, p2, p0}, Lio/mesalabs/unica/BixbyKeyActionActivity$$ExternalSyntheticLambda0;-><init>(JI)V

    const-string p0, "OneROMBixbyKey"

    invoke-direct {v0, v1, p0}, Ljava/lang/Thread;-><init>(Ljava/lang/Runnable;Ljava/lang/String;)V

    .line 111
    invoke-virtual {v0}, Ljava/lang/Thread;->start()V

    .line 112
    return-void
.end method

.method static synthetic lambda$injectKeyLater$0(JI)V
    .registers 3

    .line 105
    invoke-static {p0, p1}, Landroid/os/SystemClock;->sleep(J)V

    .line 107
    :try_start_3
    new-instance p0, Landroid/app/Instrumentation;

    invoke-direct {p0}, Landroid/app/Instrumentation;-><init>()V

    invoke-virtual {p0, p2}, Landroid/app/Instrumentation;->sendKeyDownUpSync(I)V
    :try_end_b
    .catch Ljava/lang/Exception; {:try_start_3 .. :try_end_b} :catch_c

    .line 110
    goto :goto_14

    .line 108
    :catch_c
    move-exception p0

    .line 109
    const-string p1, "OneROMBixbyKey"

    const-string p2, "Key injection failed"

    invoke-static {p1, p2, p0}, Landroid/util/Log;->e(Ljava/lang/String;Ljava/lang/String;Ljava/lang/Throwable;)I

    .line 111
    :goto_14
    return-void
.end method

.method private static launch(Landroid/content/Context;Landroid/content/Intent;)V
    .registers 3

    .line 63
    const/high16 v0, 0x10200000

    invoke-virtual {p1, v0}, Landroid/content/Intent;->addFlags(I)Landroid/content/Intent;

    .line 65
    :try_start_5
    invoke-virtual {p0, p1}, Landroid/content/Context;->startActivity(Landroid/content/Intent;)V
    :try_end_8
    .catch Landroid/content/ActivityNotFoundException; {:try_start_5 .. :try_end_8} :catch_9

    .line 68
    goto :goto_26

    .line 66
    :catch_9
    move-exception p0

    .line 67
    invoke-static {p1}, Ljava/lang/String;->valueOf(Ljava/lang/Object;)Ljava/lang/String;

    move-result-object p0

    new-instance p1, Ljava/lang/StringBuilder;

    invoke-direct {p1}, Ljava/lang/StringBuilder;-><init>()V

    const-string v0, "No activity for "

    invoke-virtual {p1, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p1

    invoke-virtual {p1, p0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p0

    invoke-virtual {p0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p0

    const-string p1, "OneROMBixbyKey"

    invoke-static {p1, p0}, Landroid/util/Log;->w(Ljava/lang/String;Ljava/lang/String;)I

    .line 69
    :goto_26
    return-void
.end method

.method private static launchCamera(Landroid/content/Context;)V
    .registers 3

    .line 72
    const-class v0, Landroid/app/KeyguardManager;

    invoke-virtual {p0, v0}, Landroid/content/Context;->getSystemService(Ljava/lang/Class;)Ljava/lang/Object;

    move-result-object v0

    check-cast v0, Landroid/app/KeyguardManager;

    .line 73
    if-eqz v0, :cond_18

    invoke-virtual {v0}, Landroid/app/KeyguardManager;->isKeyguardLocked()Z

    move-result v1

    if-eqz v1, :cond_18

    invoke-virtual {v0}, Landroid/app/KeyguardManager;->isKeyguardSecure()Z

    move-result v0

    if-eqz v0, :cond_18

    const/4 v0, 0x1

    goto :goto_19

    :cond_18
    const/4 v0, 0x0

    .line 74
    :goto_19
    new-instance v1, Landroid/content/Intent;

    if-eqz v0, :cond_20

    .line 75
    const-string v0, "android.media.action.STILL_IMAGE_CAMERA_SECURE"

    goto :goto_22

    .line 76
    :cond_20
    const-string v0, "android.media.action.STILL_IMAGE_CAMERA"

    :goto_22
    invoke-direct {v1, v0}, Landroid/content/Intent;-><init>(Ljava/lang/String;)V

    .line 74
    invoke-static {p0, v1}, Lio/mesalabs/unica/BixbyKeyActionActivity;->launch(Landroid/content/Context;Landroid/content/Intent;)V

    .line 77
    return-void
.end method

.method private run(Landroid/content/Context;Ljava/lang/String;)V
    .registers 5
    .annotation system Ldalvik/annotation/Throws;
        value = {
            Ljava/lang/Exception;
        }
    .end annotation

    .line 40
    if-nez p2, :cond_4

    const-string p2, "voice"

    .line 41
    :cond_4
    invoke-virtual {p2}, Ljava/lang/String;->hashCode()I

    move-result v0

    sparse-switch v0, :sswitch_data_64

    :cond_b
    goto :goto_3e

    :sswitch_c
    const-string v0, "torch"

    invoke-virtual {p2, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result p2

    if-eqz p2, :cond_b

    const/4 p2, 0x1

    goto :goto_3f

    :sswitch_16
    const-string v0, "media"

    invoke-virtual {p2, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result p2

    if-eqz p2, :cond_b

    const/4 p2, 0x3

    goto :goto_3f

    :sswitch_20
    const-string v0, "none"

    invoke-virtual {p2, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result p2

    if-eqz p2, :cond_b

    const/4 p2, 0x4

    goto :goto_3f

    :sswitch_2a
    const-string v0, "screenshot"

    invoke-virtual {p2, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result p2

    if-eqz p2, :cond_b

    const/4 p2, 0x2

    goto :goto_3f

    :sswitch_34
    const-string v0, "camera"

    invoke-virtual {p2, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result p2

    if-eqz p2, :cond_b

    const/4 p2, 0x0

    goto :goto_3f

    :goto_3e
    const/4 p2, -0x1

    :goto_3f
    packed-switch p2, :pswitch_data_7a

    .line 57
    new-instance p2, Landroid/content/Intent;

    const-string v0, "android.intent.action.VOICE_COMMAND"

    invoke-direct {p2, v0}, Landroid/content/Intent;-><init>(Ljava/lang/String;)V

    invoke-static {p1, p2}, Lio/mesalabs/unica/BixbyKeyActionActivity;->launch(Landroid/content/Context;Landroid/content/Intent;)V

    goto :goto_62

    .line 55
    :pswitch_4d
    goto :goto_62

    .line 52
    :pswitch_4e
    invoke-static {p1}, Lio/mesalabs/unica/BixbyKeyActionActivity;->dispatchMediaKey(Landroid/content/Context;)V

    .line 53
    goto :goto_62

    .line 49
    :pswitch_52
    const/16 p1, 0x78

    const-wide/16 v0, 0x190

    invoke-static {p1, v0, v1}, Lio/mesalabs/unica/BixbyKeyActionActivity;->injectKeyLater(IJ)V

    .line 50
    goto :goto_62

    .line 46
    :pswitch_5a
    invoke-static {p1}, Lio/mesalabs/unica/BixbyKeyActionActivity;->toggleTorch(Landroid/content/Context;)V

    .line 47
    goto :goto_62

    .line 43
    :pswitch_5e
    invoke-static {p1}, Lio/mesalabs/unica/BixbyKeyActionActivity;->launchCamera(Landroid/content/Context;)V

    .line 44
    nop

    .line 60
    :goto_62
    return-void

    nop

    :sswitch_data_64
    .sparse-switch
        -0x51863cdb -> :sswitch_34
        -0x18d27a9a -> :sswitch_2a
        0x33af38 -> :sswitch_20
        0x62f6fe4 -> :sswitch_16
        0x696d3fc -> :sswitch_c
    .end sparse-switch

    :pswitch_data_7a
    .packed-switch 0x0
        :pswitch_5e
        :pswitch_5a
        :pswitch_52
        :pswitch_4e
        :pswitch_4d
    .end packed-switch
.end method

.method private static toggleTorch(Landroid/content/Context;)V
    .registers 10
    .annotation system Ldalvik/annotation/Throws;
        value = {
            Ljava/lang/Exception;
        }
    .end annotation

    .line 80
    const-class v0, Landroid/hardware/camera2/CameraManager;

    invoke-virtual {p0, v0}, Landroid/content/Context;->getSystemService(Ljava/lang/Class;)Ljava/lang/Object;

    move-result-object v0

    check-cast v0, Landroid/hardware/camera2/CameraManager;

    .line 81
    invoke-virtual {v0}, Landroid/hardware/camera2/CameraManager;->getCameraIdList()[Ljava/lang/String;

    move-result-object v1

    array-length v2, v1

    const/4 v3, 0x0

    move v4, v3

    :goto_f
    if-ge v4, v2, :cond_4e

    aget-object v5, v1, v4

    .line 82
    invoke-virtual {v0, v5}, Landroid/hardware/camera2/CameraManager;->getCameraCharacteristics(Ljava/lang/String;)Landroid/hardware/camera2/CameraCharacteristics;

    move-result-object v6

    .line 83
    sget-object v7, Landroid/hardware/camera2/CameraCharacteristics;->FLASH_INFO_AVAILABLE:Landroid/hardware/camera2/CameraCharacteristics$Key;

    invoke-virtual {v6, v7}, Landroid/hardware/camera2/CameraCharacteristics;->get(Landroid/hardware/camera2/CameraCharacteristics$Key;)Ljava/lang/Object;

    move-result-object v7

    check-cast v7, Ljava/lang/Boolean;

    .line 84
    sget-object v8, Landroid/hardware/camera2/CameraCharacteristics;->LENS_FACING:Landroid/hardware/camera2/CameraCharacteristics$Key;

    invoke-virtual {v6, v8}, Landroid/hardware/camera2/CameraCharacteristics;->get(Landroid/hardware/camera2/CameraCharacteristics$Key;)Ljava/lang/Object;

    move-result-object v6

    check-cast v6, Ljava/lang/Integer;

    .line 85
    sget-object v8, Ljava/lang/Boolean;->TRUE:Ljava/lang/Boolean;

    invoke-virtual {v8, v7}, Ljava/lang/Boolean;->equals(Ljava/lang/Object;)Z

    move-result v7

    if-eqz v7, :cond_4b

    if-eqz v6, :cond_4b

    invoke-virtual {v6}, Ljava/lang/Integer;->intValue()I

    move-result v6

    const/4 v7, 0x1

    if-ne v6, v7, :cond_4b

    .line 87
    invoke-virtual {p0}, Landroid/content/Context;->getContentResolver()Landroid/content/ContentResolver;

    move-result-object p0

    const-string v1, "flashlight_enabled"

    invoke-static {p0, v1, v3}, Landroid/provider/Settings$Secure;->getInt(Landroid/content/ContentResolver;Ljava/lang/String;I)I

    move-result p0

    if-ne p0, v7, :cond_45

    move v3, v7

    .line 88
    :cond_45
    xor-int/lit8 p0, v3, 0x1

    invoke-virtual {v0, v5, p0}, Landroid/hardware/camera2/CameraManager;->setTorchMode(Ljava/lang/String;Z)V

    .line 89
    return-void

    .line 81
    :cond_4b
    add-int/lit8 v4, v4, 0x1

    goto :goto_f

    .line 92
    :cond_4e
    const-string p0, "OneROMBixbyKey"

    const-string v0, "No back camera with flash"

    invoke-static {p0, v0}, Landroid/util/Log;->w(Ljava/lang/String;Ljava/lang/String;)I

    .line 93
    return-void
.end method


# virtual methods
.method protected onCreate(Landroid/os/Bundle;)V
    .registers 6

    .line 26
    invoke-super {p0, p1}, Landroid/app/Activity;->onCreate(Landroid/os/Bundle;)V

    .line 27
    const/4 p1, 0x1

    invoke-virtual {p0, p1}, Lio/mesalabs/unica/BixbyKeyActionActivity;->setShowWhenLocked(Z)V

    .line 28
    invoke-virtual {p0}, Lio/mesalabs/unica/BixbyKeyActionActivity;->getIntent()Landroid/content/Intent;

    move-result-object p1

    const-string v0, "onerom_action"

    invoke-virtual {p1, v0}, Landroid/content/Intent;->getStringExtra(Ljava/lang/String;)Ljava/lang/String;

    move-result-object p1

    .line 29
    new-instance v0, Ljava/lang/StringBuilder;

    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V

    const-string v1, "action="

    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0, p1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v0

    const-string v1, "OneROMBixbyKey"

    invoke-static {v1, v0}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 31
    :try_start_29
    invoke-virtual {p0}, Lio/mesalabs/unica/BixbyKeyActionActivity;->getApplicationContext()Landroid/content/Context;

    move-result-object v0

    invoke-direct {p0, v0, p1}, Lio/mesalabs/unica/BixbyKeyActionActivity;->run(Landroid/content/Context;Ljava/lang/String;)V
    :try_end_30
    .catch Ljava/lang/Exception; {:try_start_29 .. :try_end_30} :catch_31

    .line 34
    goto :goto_48

    .line 32
    :catch_31
    move-exception v0

    .line 33
    new-instance v2, Ljava/lang/StringBuilder;

    invoke-direct {v2}, Ljava/lang/StringBuilder;-><init>()V

    const-string v3, "Failed to run action "

    invoke-virtual {v2, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v2

    invoke-virtual {v2, p1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p1

    invoke-virtual {p1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p1

    invoke-static {v1, p1, v0}, Landroid/util/Log;->e(Ljava/lang/String;Ljava/lang/String;Ljava/lang/Throwable;)I

    .line 35
    :goto_48
    invoke-virtual {p0}, Lio/mesalabs/unica/BixbyKeyActionActivity;->finish()V

    .line 36
    const/4 p1, 0x0

    invoke-virtual {p0, p1, p1}, Lio/mesalabs/unica/BixbyKeyActionActivity;->overridePendingTransition(II)V

    .line 37
    return-void
.end method
