from django.db.models import Q
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response

from teams.models import Team, TeamMember

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
    

class JoinTeamAPIView(APIView):
    def post(self, request):
        code = request.data.get("invite_code")

        try:
            team = Team.objects.get(invite_code=code)
        except Team.DoesNotExist:
            return Response({"detail": "Invalid code"}, status=400)
        
        if TeamMember.objects.filter(team=team, user=request.user).exists():
            return Response({"detail": "Already in team"}, status=400)

        TeamMember.objects.get_or_create(
            team=team,
            user=request.user,
            role="member"
        )

        return Response({"detail": "Joined team"})
