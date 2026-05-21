from rest_framework import serializers

from expenses.models import Expense, ExpenseCategory


class ExpenseCategoryReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения категорий расходов."""
    total = serializers.DecimalField(max_digits=13, decimal_places=2, read_only=True)

    team_name = serializers.CharField(
        source="team.name",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = ExpenseCategory
        fields = (
            "id",
            "name",
            "total",
            "team_name",
        )


class ExpenseCategoryWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/редактирования категории расходов."""
    class Meta:
        model = ExpenseCategory
        fields = ("name",)


class ExpenseReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения расхода с вложенной категорией."""
    category = ExpenseCategoryReadSerializer(read_only=True)

    team_name = serializers.CharField(
        source="team.name",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = Expense
        fields = (
            "id",
            "title",
            "category",
            "description",
            "amount",
            "currency",
            "exchange_rate",
            "amount_rub",
            "team_name",
            "date",
            "created_at",
            "updated_at",
        )


class ExpenseWriteSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания и редактирования расхода.

    Кастомная валидация категории в зависимости от того,
    является ли расход командным или личным.
    """

    class Meta:
        model = Expense
        fields = ("title", "description", "amount", "currency", "date", "category")

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Сумма расхода должна быть больше нуля.")
        return value

    def validate_category(self, category):
        request = self.context["request"]
        team_pk = self.context["view"].kwargs.get("team_pk")

        if team_pk:
            if category.team_id != int(team_pk):
                raise serializers.ValidationError("Неизвестная категория.")
        else:
            if category.user_id != request.user.id:
                raise serializers.ValidationError("Неизвестная категория.")

        return category
