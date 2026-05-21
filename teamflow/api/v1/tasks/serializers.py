from rest_framework import serializers

from tasks.models import Task, TaskCategory
from teams.models import TeamMember


class TaskCategoryReadSerializer(serializers.ModelSerializer):
    """Сериализатор категории задач с агрегированным количеством задач."""
    total = serializers.IntegerField(read_only=True)

    team_name = serializers.CharField(
        source="team.name",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = TaskCategory
        fields = (
            "id",
            "name",
            "total",
            "team_name",
        )


class TaskCategoryWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/редактирования категории задач."""
    class Meta:
        model = TaskCategory
        fields = ("name",)


class TaskReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения задачи с вложенной категорией."""
    category = TaskCategoryReadSerializer(read_only=True)

    team_name = serializers.CharField(
        source="team.name",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = Task
        fields = (
            "id",
            "title",
            "category",
            "description",
            "status",
            "priority",
            "deadline",
            "team_name",
            "assigned_to",
            "created_at",
            "updated_at",
        )


class TaskWriteSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания и редактирования задачи.

    Содержит кастомную валидацию:
    assigned_to можно указывать только в командных задачах
    assigned_to должен быть участником команды
    category должна принадлежать той же команде/пользователю
    """

    class Meta:
        model = Task
        fields = (
            "title",
            "description",
            "deadline",
            "status",
            "priority",
            "category",
            "assigned_to",
        )

    def validate_assigned_to(self, assigned_to):
        team_pk = self.context["view"].kwargs.get("team_pk")
        if assigned_to and not team_pk:
            raise serializers.ValidationError(
                "Невозможно назначить исполнителя для личной задачи."
            )
        if assigned_to not in TeamMember.objects.filter(team_id=team_pk).values_list(
            "user", flat=True
        ):
            raise serializers.ValidationError("Такого пользователя нету в команде.")
        return assigned_to

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
