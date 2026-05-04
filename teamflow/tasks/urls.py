from django.urls import path

from . import views

app_name = "tasks"


urlpatterns = [
    path("", views.TaskListView.as_view(), name="task_list"),
    path("add/", views.TaskCreateView.as_view(), name="task_create"),
    path("<int:pk>/", views.TaskDetailView.as_view(), name="task_detail"),
    path("<int:pk>/edit/", views.TaskUpdateView.as_view(), name="task_update"),
    path("<int:pk>/delete/", views.TaskDeleteView.as_view(), name="task_delete"),
    path(
        "<int:pk>/mark-done/", views.TaskMarkAsDoneView.as_view(), name="task_mark_done"
    ),
    path("categories/", views.TaskCategoryListView.as_view(), name="category_list"),
    path(
        "category/add/", views.TaskCategoryCreateView.as_view(), name="category_create"
    ),
    path(
        "category/<int:pk>/edit/",
        views.TaskCategoryUpdateView.as_view(),
        name="category_update",
    ),
    path(
        "category/<int:pk>/delete/",
        views.TaskCategoryDeleteView.as_view(),
        name="task_category_delete",
    ),
]
