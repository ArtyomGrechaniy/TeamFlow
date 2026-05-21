from rest_framework.permissions import BasePermission

from teams.models import TeamMember


class IsOwnerOrTeamMember(BasePermission):
    """
    Личные объекты доступны владельцу без ограничений
    Командные объекты:
        list/retrieve — любой участник команды
        create/update/partial_update/destroy — только администратор или владелец
    """
    def has_permission(self, request, view):
        team_pk = view.kwargs.get("team_pk")
        if not team_pk:
            return view.action in [
                "list",
                "retrieve",
                "create",
                "update",
                "partial_update",
                "destroy",
            ]

        if view.action in ["list", "retrieve"]:
            return TeamMember.objects.filter(
                team_id=team_pk, user=request.user
            ).exists()

        if view.action in ["create", "update", "partial_update", "destroy"]:
            return TeamMember.objects.filter(
                team_id=team_pk,
                user=request.user,
                role__in=["admin", "owner"],
            ).exists()

        return False

    def has_object_permission(self, request, view, obj):
        if obj.user == request.user:
            return True

        if obj.team:
            if view.action in ["update", "partial_update", "destroy"]:
                return TeamMember.objects.filter(
                    user=request.user, team_id=obj.team_id, role__in=["admin", "owner"]
                ).exists()
            if view.action == "retrieve":
                return TeamMember.objects.filter(
                    user=request.user,
                    team_id=obj.team_id,
                ).exists()

        return False
