from django.db.models import Count, Q
from rest_framework import viewsets

from api.v1.permissions import IsOwnerOrTeamMember
from tasks.models import Task, TaskCategory
from teams.models import TeamMember

from .serializers import (
    TaskCategoryReadSerializer,
    TaskCategoryWriteSerializer,
    TaskReadSerializer,
    TaskWriteSerializer,
)


class TaskCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet для категорий задач.

    Поддерживает как командные, так и личные категории.
    Добавляет агрегированное поле total.
    """
    permission_classes = [IsOwnerOrTeamMember]

    def get_queryset(self):
        qs = TaskCategory.objects.select_related("team", "user").annotate(
            total=Count("tasks")
        )
        user = self.request.user
        team_pk = self.kwargs.get("team_pk")

        if team_pk:
            return qs.filter(team_id=team_pk)

        return qs.filter(user=user)

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return TaskCategoryReadSerializer

        if self.action in ["create", "update", "partial_update"]:
            return TaskCategoryWriteSerializer

        return TaskCategoryReadSerializer

    def perform_create(self, serializer):
        team_pk = self.kwargs.get("team_pk")

        if team_pk:
            serializer.save(team_id=team_pk, user=None)
            return
        serializer.save(team_id=None, user=self.request.user)


class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet для задач.

    В командном режиме (с team_pk) — только задачи команды.
    В личном режиме — личные задачи + все задачи из команд, где пользователь состоит.
    """
    permission_classes = [IsOwnerOrTeamMember]

    def get_queryset(self):
        qs = Task.objects.select_related("category", "team", "user", "assigned_to")
        user = self.request.user
        team_pk = self.kwargs.get("team_pk")

        if team_pk:
            return qs.filter(team_id=team_pk)

        user_teams = TeamMember.objects.filter(user=user).values_list(
            "team_id", flat=True
        )

        return qs.filter(Q(user=user) | Q(team_id__in=user_teams))

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return TaskReadSerializer

        if self.action in ["create", "update", "partial_update"]:
            return TaskWriteSerializer

        return TaskReadSerializer

    def perform_create(self, serializer):
        team_pk = self.kwargs.get("team_pk")

        if team_pk:
            serializer.save(team_id=team_pk, user=None)
            return
        serializer.save(team_id=None, user=self.request.user)
