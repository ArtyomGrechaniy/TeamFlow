from rest_framework.permissions import BasePermission

from teams.models import TeamMember


class IsTeamOwner(BasePermission):
    """
    Разрешает обновление и удаление только владельцу команды.
    """

    def has_object_permission(self, request, view, obj):
        if view.action in ["update", "partial_update", "destroy"]:
            return TeamMember.objects.filter(
                team=obj,
                user=request.user,
                role_="owner",
            ).exists()

        return False
