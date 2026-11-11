.class public Lio/mesalabs/unica/settings/AboutHomepagePreference;
.super Lcom/android/settings/widget/HomepagePreference;
.source "AboutHomepagePreference.java"

.implements Landroid/view/View$OnLongClickListener;

.method public constructor <init>(Landroid/content/Context;Landroid/util/AttributeSet;)V
    .locals 0

    invoke-direct {p0, p1, p2}, Lcom/android/settings/widget/HomepagePreference;-><init>(Landroid/content/Context;Landroid/util/AttributeSet;)V
    return-void
.end method

.method public onBindViewHolder(Landroidx/preference/PreferenceViewHolder;)V
    .locals 1

    invoke-super {p0, p1}, Lcom/android/settings/widget/HomepagePreference;->onBindViewHolder(Landroidx/preference/PreferenceViewHolder;)V
    iget-object v0, p1, Landroidx/recyclerview/widget/RecyclerView$ViewHolder;->itemView:Landroid/view/View;
    invoke-virtual {v0, p0}, Landroid/view/View;->setOnLongClickListener(Landroid/view/View$OnLongClickListener;)V
    return-void
.end method

.method public onLongClick(Landroid/view/View;)Z
    .locals 2

    new-instance v0, Landroid/content/Intent;
    const-string v1, "android.settings.APPLICATION_DEVELOPMENT_SETTINGS"
    invoke-direct {v0, v1}, Landroid/content/Intent;-><init>(Ljava/lang/String;)V
    invoke-virtual {p0}, Landroidx/preference/Preference;->getContext()Landroid/content/Context;
    move-result-object v1
    invoke-virtual {v1, v0}, Landroid/content/Context;->startActivity(Landroid/content/Intent;)V
    const/4 v0, 0x1
    return v0
.end method