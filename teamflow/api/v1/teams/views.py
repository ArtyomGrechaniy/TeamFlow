from django.db.models import Q
from rest_framework import viewsets

from teams.models import Team

from .permissions import IsTeamOwner
from .serializers import (
    TeamReadSerializer,
    TeamWriteSerializer,
)


class TeamViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления командами.
    """
    permission_classes = [IsTeamOwner]

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return TeamReadSerializer
        if self.action in ["create", "update", "partial_update"]:
            return TeamWriteSerializer
        return TeamReadSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_queryset(self):
        user = self.request.user
        return (
            Team.objects.filter(Q(owner=user) | Q(members__user=user))
            .distinct()
            .prefetch_related("members__user")
        )
