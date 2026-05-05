from django.contrib import admin
from django.utils.text import Truncator

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "first_name",
        "last_name",
        "short_bio",
        "avatar",
        "telegram",
        "github_url",
        "is_statistics_public"
    )
    search_fields = (
        "user__username",
        "first_name",
        "last_name",
    )
    
    ordering = ("user__username",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user")
    
    @admin.display(description="Имя")
    def first_name(self, obj):
        return obj.user.first_name
    
    @admin.display(description="Фамилия")
    def last_name(self, obj):
        return obj.user.last_name

    @admin.display(description="О себе")
    def short_bio(self, obj):
        return Truncator(obj.bio).chars(100) if obj.bio else "-"