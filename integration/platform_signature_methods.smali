# Derived from ImpulseROM, GPL-3.0; original authorship retained in pinned patch.
.method public static isSignedWithCustomPlatformKey(Lcom/android/internal/pm/parsing/pkg/ParsedPackage;)Z
    .registers 4

    invoke-static {p0}, Lcom/android/server/pm/ScanPackageUtils;->isAllowedCustomPlatformPackage(Lcom/android/internal/pm/parsing/pkg/ParsedPackage;)Z

    move-result v0

    if-eqz v0, :cond_false

    new-instance v0, Landroid/content/pm/Signature;

    const-string v1, "CONFIG_CUSTOM_PLATFORM_SIGNATURE"

    invoke-direct {v0, v1}, Landroid/content/pm/Signature;-><init>(Ljava/lang/String;)V

    const/4 v1, 0x1

    new-array v1, v1, [Landroid/content/pm/Signature;

    const/4 v2, 0x0

    aput-object v0, v1, v2

    invoke-interface {p0}, Lcom/android/internal/pm/parsing/pkg/ParsedPackage;->getSigningDetails()Landroid/content/pm/SigningDetails;

    move-result-object p0

    invoke-virtual {p0}, Landroid/content/pm/SigningDetails;->getSignatures()[Landroid/content/pm/Signature;

    move-result-object p0

    invoke-static {v1, p0}, Lcom/android/server/pm/PackageManagerServiceUtils;->compareSignatureArrays([Landroid/content/pm/Signature;[Landroid/content/pm/Signature;)I

    move-result p0

    if-nez p0, :cond_false

    const/4 p0, 0x1

    return p0

    :cond_false
    const/4 p0, 0x0

    return p0
.end method

.method public static setCustomSignatures(Lcom/android/internal/pm/parsing/pkg/ParsedPackage;Lcom/android/server/pm/pkg/AndroidPackage;)V
    .registers 3

    invoke-static {p0}, Lcom/android/server/pm/ScanPackageUtils;->isSignedWithCustomPlatformKey(Lcom/android/internal/pm/parsing/pkg/ParsedPackage;)Z

    move-result v0

    if-eqz v0, :cond_return

    if-eqz p1, :cond_return

    invoke-interface {p1}, Lcom/android/server/pm/pkg/AndroidPackage;->getSigningDetails()Landroid/content/pm/SigningDetails;

    move-result-object p1

    invoke-interface {p0, p1}, Lcom/android/internal/pm/parsing/pkg/ParsedPackage;->setSigningDetails(Landroid/content/pm/SigningDetails;)Lcom/android/internal/pm/parsing/pkg/ParsedPackage;

    :cond_return
    return-void
.end method
