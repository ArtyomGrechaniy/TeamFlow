from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import TaskCategoryViewSet, TaskViewSet

router = DefaultRouter()
router.register("tasks", TaskViewSet, basename="tasks")
router.register(
    "task_categories",
    TaskCategoryViewSet,
    basename="task_categories",
)


task_list = TaskViewSet.as_view(
    {
        "get": "list",
        "post": "create",
    }
)

task_detail = TaskViewSet.as_view(
    {
        "get": "retrieve",
        "put": "update",
        "patch": "partial_update",
        "delete": "destroy",
    }
)

task_category_list = TaskCategoryViewSet.as_view(
    {
        "get": "list",
        "post": "create",
    }
)

task_category_detail = TaskCategoryViewSet.as_view(
    {
        "get": "retrieve",
        "put": "update",
        "patch": "partial_update",
        "delete": "destroy",
    }
)


team_urls = [
    path(
        "tasks/",
        task_list,
        name="team_tasks_list",
    ),
    path(
        "tasks/<int:pk>/",
        task_detail,
        name="team_tasks_detail",
    ),
    path(
        "task_categories/",
        task_category_list,
        name="team_task_categories_list",
    ),
    path(
        "task_categories/<int:pk>/",
        task_category_detail,
        name="team_task_categories_detail",
    ),
]


urlpatterns = [
    path("", include(router.urls)),
    path("teams/<int:team_pk>/", include(team_urls)),
]
