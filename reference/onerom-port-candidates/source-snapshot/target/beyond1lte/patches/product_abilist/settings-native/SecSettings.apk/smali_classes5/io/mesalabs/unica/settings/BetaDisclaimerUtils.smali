.class public Lio/mesalabs/unica/settings/BetaDisclaimerUtils;
.super Ljava/lang/Object;
.source "BetaDisclaimerUtils.java"


# static fields
.field private static final AUTHORIZED_DEVICES:[Ljava/lang/String;


# direct methods
.method static constructor <clinit>()V
    .registers 3

    .line 12
    const/4 v0, 0x1

    new-array v0, v0, [Ljava/lang/String;

    const/4 v1, 0x0

    const-string v2, "RF8M71H6WBX"

    aput-object v2, v0, v1

    sput-object v0, Lio/mesalabs/unica/settings/BetaDisclaimerUtils;->AUTHORIZED_DEVICES:[Ljava/lang/String;

    return-void
.end method

.method public constructor <init>()V
    .registers 1

    .line 11
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method

.method public static isDeviceAuthorized()Z
    .registers 7

    .line 18
    const-string v0, ""

    const/4 v1, 0x1

    :try_start_3
    const-string v2, "ro.serialno"

    invoke-static {v2, v0}, Landroid/os/SystemProperties;->get(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v2

    .line 19
    if-eqz v2, :cond_11

    invoke-virtual {v2}, Ljava/lang/String;->isEmpty()Z

    move-result v3

    if-eqz v3, :cond_17

    .line 20
    :cond_11
    const-string v2, "ro.boot.serialno"

    invoke-static {v2, v0}, Landroid/os/SystemProperties;->get(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v2

    .line 22
    :cond_17
    if-eqz v2, :cond_34

    invoke-virtual {v2}, Ljava/lang/String;->isEmpty()Z

    move-result v0

    if-eqz v0, :cond_20

    goto :goto_34

    .line 25
    :cond_20
    sget-object v0, Lio/mesalabs/unica/settings/BetaDisclaimerUtils;->AUTHORIZED_DEVICES:[Ljava/lang/String;

    array-length v3, v0

    const/4 v4, 0x0

    const/4 v5, 0x0

    :goto_25
    if-ge v5, v3, :cond_33

    aget-object v6, v0, v5

    .line 26
    invoke-virtual {v6, v2}, Ljava/lang/String;->equalsIgnoreCase(Ljava/lang/String;)Z

    move-result v6
    :try_end_2d
    .catchall {:try_start_3 .. :try_end_2d} :catchall_35

    if-eqz v6, :cond_30

    .line 27
    return v1

    .line 25
    :cond_30
    add-int/lit8 v5, v5, 0x1

    goto :goto_25

    .line 30
    :cond_33
    return v4

    .line 23
    :cond_34
    :goto_34
    return v1

    .line 31
    :catchall_35
    move-exception v0

    .line 32
    return v1
.end method

.method public static showDisclaimerIfNeeded(Landroid/content/Context;)V
    .registers 7

    .line 37
    if-nez p0, :cond_3

    return-void

    .line 39
    :cond_3
    :try_start_3
    invoke-static {}, Lio/mesalabs/unica/settings/BetaDisclaimerUtils;->isDeviceAuthorized()Z

    move-result v0
    :try_end_7
    .catchall {:try_start_3 .. :try_end_7} :catchall_84

    const-string v1, "Contact @DaManMikey"

    const/4 v2, 0x0

    if-nez v0, :cond_4f

    .line 40
    :try_start_c
    const-string v0, "ro.serialno"

    const-string v3, "Unknown"

    invoke-static {v0, v3}, Landroid/os/SystemProperties;->get(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v0

    .line 41
    new-instance v3, Landroid/app/AlertDialog$Builder;

    invoke-direct {v3, p0}, Landroid/app/AlertDialog$Builder;-><init>(Landroid/content/Context;)V

    .line 42
    const-string v4, "Unauthorized Beta Device"

    invoke-virtual {v3, v4}, Landroid/app/AlertDialog$Builder;->setTitle(Ljava/lang/CharSequence;)Landroid/app/AlertDialog$Builder;

    .line 43
    new-instance v4, Ljava/lang/StringBuilder;

    invoke-direct {v4}, Ljava/lang/StringBuilder;-><init>()V

    const-string v5, "This test preview of OneROM 9.0 is restricted to authorized testers.\n\nDevice ID: "

    invoke-virtual {v4, v5}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v4

    invoke-virtual {v4, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    const-string v4, "\n\nPlease contact @DaManMikey on Telegram to request access for your device."

    invoke-virtual {v0, v4}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v0

    invoke-virtual {v3, v0}, Landroid/app/AlertDialog$Builder;->setMessage(Ljava/lang/CharSequence;)Landroid/app/AlertDialog$Builder;

    .line 48
    invoke-virtual {v3, v2}, Landroid/app/AlertDialog$Builder;->setCancelable(Z)Landroid/app/AlertDialog$Builder;

    .line 49
    new-instance v0, Lio/mesalabs/unica/settings/BetaDisclaimerUtils$1;

    invoke-direct {v0, p0}, Lio/mesalabs/unica/settings/BetaDisclaimerUtils$1;-><init>(Landroid/content/Context;)V

    invoke-virtual {v3, v1, v0}, Landroid/app/AlertDialog$Builder;->setPositiveButton(Ljava/lang/CharSequence;Landroid/content/DialogInterface$OnClickListener;)Landroid/app/AlertDialog$Builder;

    .line 59
    const-string p0, "Close"

    const/4 v0, 0x0

    invoke-virtual {v3, p0, v0}, Landroid/app/AlertDialog$Builder;->setNegativeButton(Ljava/lang/CharSequence;Landroid/content/DialogInterface$OnClickListener;)Landroid/app/AlertDialog$Builder;

    .line 60
    invoke-virtual {v3}, Landroid/app/AlertDialog$Builder;->show()Landroid/app/AlertDialog;

    .line 61
    return-void

    .line 64
    :cond_4f
    invoke-virtual {p0}, Landroid/content/Context;->getContentResolver()Landroid/content/ContentResolver;

    move-result-object v0

    const-string v3, "onerom_beta_disclaimer_shown"

    invoke-static {v0, v3, v2}, Landroid/provider/Settings$System;->getInt(Landroid/content/ContentResolver;Ljava/lang/String;I)I

    move-result v0

    .line 65
    if-eqz v0, :cond_5c

    .line 66
    return-void

    .line 69
    :cond_5c
    new-instance v0, Landroid/app/AlertDialog$Builder;

    invoke-direct {v0, p0}, Landroid/app/AlertDialog$Builder;-><init>(Landroid/content/Context;)V

    .line 70
    const-string v3, "OneROM Beta Software"

    invoke-virtual {v0, v3}, Landroid/app/AlertDialog$Builder;->setTitle(Ljava/lang/CharSequence;)Landroid/app/AlertDialog$Builder;

    .line 71
    const-string v3, "You are using beta software (OneROM 9.0 Dev Beta).\n\nThis ROM is currently in active development and not yet stable enough for public release. You may experience bugs, crashes, or unexpected behavior.\n\nFor support, questions, or bug reports, please contact @DaManMikey on Telegram."

    invoke-virtual {v0, v3}, Landroid/app/AlertDialog$Builder;->setMessage(Ljava/lang/CharSequence;)Landroid/app/AlertDialog$Builder;

    .line 76
    invoke-virtual {v0, v2}, Landroid/app/AlertDialog$Builder;->setCancelable(Z)Landroid/app/AlertDialog$Builder;

    .line 77
    new-instance v2, Lio/mesalabs/unica/settings/BetaDisclaimerUtils$2;

    invoke-direct {v2, p0}, Lio/mesalabs/unica/settings/BetaDisclaimerUtils$2;-><init>(Landroid/content/Context;)V

    invoke-virtual {v0, v1, v2}, Landroid/app/AlertDialog$Builder;->setPositiveButton(Ljava/lang/CharSequence;Landroid/content/DialogInterface$OnClickListener;)Landroid/app/AlertDialog$Builder;

    .line 88
    const-string v1, "I Understand"

    new-instance v2, Lio/mesalabs/unica/settings/BetaDisclaimerUtils$3;

    invoke-direct {v2, p0}, Lio/mesalabs/unica/settings/BetaDisclaimerUtils$3;-><init>(Landroid/content/Context;)V

    invoke-virtual {v0, v1, v2}, Landroid/app/AlertDialog$Builder;->setNegativeButton(Ljava/lang/CharSequence;Landroid/content/DialogInterface$OnClickListener;)Landroid/app/AlertDialog$Builder;

    .line 96
    invoke-virtual {v0}, Landroid/app/AlertDialog$Builder;->show()Landroid/app/AlertDialog;
    :try_end_83
    .catchall {:try_start_c .. :try_end_83} :catchall_84

    .line 99
    goto :goto_85

    .line 97
    :catchall_84
    move-exception p0

    .line 100
    :goto_85
    return-void
.end method
