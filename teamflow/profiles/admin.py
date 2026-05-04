from django.contrib import admin
from django.utils.text import Truncator

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "short_bio",
        "avatar",
        "telegram",
        "github_url",
        "is_statistics_public"
    )
    search_fields = (
        "user__username",
        "bio",
    )
    list_select_related = (
        "user",
    )

    @admin.display(description="О себе")
    def short_bio(self, obj):
        if not obj.bio:
            return "-"

        return Truncator(obj.bio).chars(100)