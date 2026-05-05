from django.contrib import admin
from django.utils.text import Truncator

from .models import CurrencyRate, Expense, ExpenseCategory


@admin.register(CurrencyRate)
class CurrencyRateAdmin(admin.ModelAdmin):
    list_display = (
        "currency",
        "rate",
        "date"
    )
    search_fields = ("currency",)
    ordering = ("-rate",)


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "user",
        "team"
    )
    search_fields = (
        "name",
        "slug"
    )
    list_filter = ("team",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user", "team")

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ("team", "user")
        return ()



@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "short_description",
        "amount",
        "currency",
        "exchange_rate",
        "amount_rub",
        "user",
        "team",
        "category",
        "date",
        "created_at",
        "updated_at"
    )
    list_filter = (
        "category",
        "team",
        "currency"
    )
    ordering = (
        "-updated_at",
        "amount_rub"
    )
    search_fields = (
        "title",
        "description"
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "user", "team", "category"
        )
    
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ("team", "user")
        return ()

    @admin.display(description="Описание")
    def short_description(self, obj):
        if obj.description:
            return Truncator(obj.description).chars(100)