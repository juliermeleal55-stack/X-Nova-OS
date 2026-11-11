from pathlib import Path
import re
import sys


METHOD = r""".method public static setDisplayMode(Ljava/lang/String;Landroid/view/Display;)V
    .registers 16

    if-eqz p0, :s10_resolution_done

    :s10_resolution_try
    invoke-static {p0}, Ljava/lang/Integer;->parseInt(Ljava/lang/String;)I
    move-result v0

    const/16 v1, 0x5a0
    const/16 v2, 0x230
    if-eqz v0, :s10_resolution_hd
    const/4 v4, 0x1
    if-eq v0, v4, :s10_resolution_fhd
    const/4 v4, 0x2
    if-ne v0, v4, :s10_resolution_done
    goto :s10_resolution_size

    :s10_resolution_fhd
    const/16 v1, 0x438
    const/16 v2, 0x1a4
    goto :s10_resolution_size

    :s10_resolution_hd
    const/16 v1, 0x2d0
    const/16 v2, 0x118

    :s10_resolution_size
    mul-int/lit8 v3, v1, 0x13
    div-int/lit8 v3, v3, 0x9
    invoke-static {}, Landroid/view/WindowManagerGlobal;->getWindowManagerService()Landroid/view/IWindowManager;
    move-result-object v6
    const/4 v7, 0x0
    move v8, v1
    move v9, v3
    move v10, v2
    const/4 v11, 0x1
    const/4 v12, -0x1
    invoke-interface/range {v6 .. v12}, Landroid/view/IWindowManager;->setForcedDisplaySizeDensity(IIIIZI)V
    :s10_resolution_try_end
    .catch Ljava/lang/Exception; {:s10_resolution_try .. :s10_resolution_try_end} :s10_resolution_error

    :s10_resolution_done
    return-void

    :s10_resolution_error
    move-exception v0
    const-string v1, "S10Resolution"
    const-string v2, "Unable to apply resolution"
    invoke-static {v1, v2, v0}, Landroid/util/Log;->e(Ljava/lang/String;Ljava/lang/String;Ljava/lang/Throwable;)I
    return-void
.end method"""


def main() -> None:
    directory = Path(sys.argv[1]) / "com/samsung/android/settings/display"
    utility = directory / "SecDisplayUtils.smali"
    source = utility.read_text()
    source, count = re.subn(
        r"\.method public static setDisplayMode\(Ljava/lang/String;Landroid/view/Display;\)V.*?\.end method",
        lambda match: METHOD,
        source,
        flags=re.S,
    )
    if count != 1:
        raise ValueError("Expected exactly one resolution apply method")
    fragment = directory / "ScreenResolutionFragment.smali"
    fragment_source = fragment.read_text()
    anchor = "    iput-object v1, p0, Lcom/samsung/android/settings/display/ScreenResolutionFragment;->mScreenResolutionButton:Lcom/samsung/android/settings/widget/SecHorizontalRadioPreference;"
    initialization = """

    iget v2, p0, Lcom/samsung/android/settings/display/ScreenResolutionFragment;->mScreenResolution:I
    invoke-static {v2}, Ljava/lang/String;->valueOf(I)Ljava/lang/String;
    move-result-object v2
    invoke-virtual {v1, v2}, Lcom/samsung/android/settings/widget/SecHorizontalRadioPreference;->setValue(Ljava/lang/String;)V
"""
    if fragment_source.count(anchor) != 1:
        raise ValueError("Expected exactly one resolution radio initialization")
    if initialization not in fragment_source:
        fragment_source = fragment_source.replace(anchor, anchor + initialization, 1)
    removal = "    invoke-virtual {p0, p1}, Lcom/android/settings/SettingsPreferenceFragment;->removePreference(Ljava/lang/String;)Z"
    section_start = fragment_source.index(anchor)
    section_end = fragment_source.index("    new-instance p1, Landroid/graphics/Point;", section_start)
    section = fragment_source[section_start:section_end]
    if removal in section:
        section = section.replace(removal, "", 1)
        fragment_source = fragment_source[:section_start] + section + fragment_source[section_end:]
    utility.write_text(source)
    fragment.write_text(fragment_source)


if __name__ == "__main__":
    main()