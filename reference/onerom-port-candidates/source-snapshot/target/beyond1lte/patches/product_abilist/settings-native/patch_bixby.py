#!/usr/bin/env python3
"""Route every Bixby key action through BixbyKeyActionActivity via the generic
start-activity key customization path (works for single, double and long press)."""
import re
import sys

f = sys.argv[1] + "/io/mesalabs/unica/settings/extra/BixbyKeyActionPreferenceController.smali"
s = open(f).read()

NEW = """.method private applyAction(Ljava/lang/String;I)V
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

    :try_start_0
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
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    return-void

    :catch_0
    move-exception v0

    const-string v1, "OneROMBixbyKey"

    const-string v2, "Unable to register key customization"

    invoke-static {v1, v2, v0}, Landroid/util/Log;->e(Ljava/lang/String;Ljava/lang/String;Ljava/lang/Throwable;)I

    return-void
.end method"""

pat = re.compile(r"\.method private applyAction\(Ljava/lang/String;I\)V.*?\.end method", re.S)
assert len(pat.findall(s)) == 1
s = pat.sub(lambda m: NEW, s)
open(f, "w").write(s)
print("applyAction replaced in", f)
