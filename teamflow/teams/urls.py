from django.urls import include, path

from . import views

app_name = "teams"

urlpatterns = [
    # Основной CRUD команд.
    path("", views.TeamListView.as_view(), name="team_list"),
    path("create/", views.TeamCreateView.as_view(), name="team_create"),
    path("<int:pk>/", views.TeamDetailView.as_view(), name="team_detail"),
    path("<int:pk>/edit/", views.TeamUpdateView.as_view(), name="team_update"),
    path("<int:pk>/delete/", views.TeamDeleteView.as_view(), name="team_delete"),

    # Командные разделы расходов и задач используют team_id в namespace teams.
    path("<int:team_id>/expenses/", include(("expenses.urls"))),
    path("<int:team_id>/tasks/", include(("tasks.urls"))),

    # Управление участием пользователя в команде.
    path("join/", views.TeamJoinView.as_view(), name="team_join"),
    path("<int:pk>/leave/", views.TeamLeaveView.as_view(), name="team_leave"),

    # Управление составом и ролями участников.
    path(
        "<int:pk>/members/", views.TeamMemberListView.as_view(), name="team_member_list"
    ),
    path(
        "<int:pk>/members/<int:user_id>/kick/",
        views.TeamMemberKickView.as_view(),
        name="team_member_kick",
    ),
    path(
        "<int:pk>/members/<int:user_id>/role/",
        views.TeamMemberRoleChangeView.as_view(),
        name="team_member_role",
    ),
]
