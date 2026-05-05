from django.contrib import admin
from django.utils.text import Truncator

from .models import Task, TaskCategory


@admin.register(TaskCategory)
class TaskCategoryAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "user",
        "team"
    )
    ordering = ("team__name", "name")
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user", "team")

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ("team", "user")
        return ()


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "short_description",
        "status",
        "priority",
        "deadline",
        "user",
        "team",
        "category",
        "assigned_to",
        "created_at",
        "updated_at"
    )
    list_filter = (
        "category",
        "team",
        "user",
        "assigned_to"
    )
    ordering = (
        "-deadline",
        "-updated_at"
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "user", "team", "category"
        )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ("team", "user")
    
    @admin.display(description='Описание')
    def short_description(self, obj):
        if obj.description:
            return Truncator(obj.description).chars(100)

