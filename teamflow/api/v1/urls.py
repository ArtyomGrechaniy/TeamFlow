from django.urls import include, path
from rest_framework.response import Response
from rest_framework.views import APIView

from api.v1.teams.views import JoinTeamAPIView

class CustomAPIRoot(APIView):
    """
    Красивая корневая страница API v1
    """

    def get(self, request, format=None):
        base = request.build_absolute_uri()

        return Response(
            {
                "teams": f"{base}teams/",
                "tasks": f"{base}tasks/",
                "task_categories": f"{base}task_categories/",
                "expenses": f"{base}expenses/",
                "expense_categories": f"{base}expense_categories/",
            }
        )


urlpatterns = [
    path("teams/join/", JoinTeamAPIView.as_view()),
    path("", CustomAPIRoot.as_view(), name="api-root"),
    path("", include("api.v1.teams.urls")),
    path("", include("api.v1.tasks.urls")),
    path("", include("api.v1.expenses.urls")),
]
