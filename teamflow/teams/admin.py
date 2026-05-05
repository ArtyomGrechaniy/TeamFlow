from django.contrib import admin
from django.utils.text import Truncator

from .models import Team, TeamMember


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "short_description",
        "owner",
        "invite_code"
    )
    search_fields = ("name", "description")
    list_filter = ("owner",)
    ordering = ("name",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("owner")

    @admin.display(description="Описание")
    def short_description(self, obj):
        if obj.description:
            return Truncator(obj.description).chars(100) if obj.description else '-'


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = (
        "team",
        "user",
        "role",
        "joined_at"
    )
    search_fields = ("user__username",)
    list_filter = ("team", "role")
    ordering = ("-joined_at",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("team", "user")