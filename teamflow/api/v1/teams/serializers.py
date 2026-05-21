from rest_framework import serializers

from teams.models import Team, TeamMember


class TeamMemberReadSerializer(serializers.ModelSerializer):
    """Сериализатор участника команды."""

    username = serializers.CharField(
        source="user.username",
        read_only=True,
    )

    class Meta:
        model = TeamMember
        fields = (
            "id",
            "username",
            "role",
        )


class TeamReadSerializer(serializers.ModelSerializer):
    """
    Сериализатор чтения команды.
    """

    members = TeamMemberReadSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Team
        fields = (
            "name",
            "owner",
            "description",
            "invite_code",
            "members",
            "created_at",
        )


class TeamWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и редактирования команды."""

    class Meta:
        model = Team
        fields = (
            "name",
            "description",
        )
