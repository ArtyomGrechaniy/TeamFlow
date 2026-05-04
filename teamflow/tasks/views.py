from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import Http404
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from core.mixins import (
    DeleteContextMixin,
    FormContextMixin,
    TeamAdminAccessMixin,
    TeamMemberAccessMixin,
    UserTeamObjectQuerysetMixin,
    OwnershipMixin
)
from teams.models import Team, TeamMember

from .forms import TaskCategoryForm, TaskForm
from .models import Task, TaskCategory

User = get_user_model()


# ====================== МИКСИНЫ ======================
class TaskMixin(LoginRequiredMixin):
    """Добавляет общие настройки и данные формы для views задач."""
    model = Task
    success_url = reverse_lazy("tasks:task_list")

    def get_form_kwargs(self):
        """Передаёт в форму команду задачи или текущего пользователя."""
        kwargs = super().get_form_kwargs()
        team_id = self.kwargs.get("team_id")

        if team_id:
            kwargs["team_id"] = team_id
        elif getattr(self, "object", None) and self.object.team_id:
            kwargs["team_id"] = self.object.team_id
        else:
            kwargs["user"] = self.request.user

        return kwargs


# ====================== CRUD ======================
class TaskListView(TeamMemberAccessMixin, ListView):
    """Показывает список личных и командных задач."""
    model = Task
    template_name = "tasks/task_list.html"
    context_object_name = "tasks"
    paginate_by = 20

    def get_queryset(self):
        """Фильтрует задачи по доступу, параметрам запроса и сортировке."""
        user = self.request.user
        team_id = self.kwargs.get("team_id")
        queryset = Task.objects.all().select_related("category", "team", "assigned_to")

        if team_id:
            # Задачи выбранной команды.
            queryset = queryset.filter(team_id=team_id)
        else:
            # Личные задачи и задачи команд пользователя.
            user_teams = TeamMember.objects.filter(user=user).values_list(
                "team", flat=True
            )
            queryset = queryset.filter(Q(user=user) | Q(team__in=user_teams))

        status = self.request.GET.get("status")
        if status:
            try:
                queryset = queryset.filter(status=int(status))
            except ValueError:
                pass

        priority = self.request.GET.get("priority")
        if priority:
            try:
                queryset = queryset.filter(priority=int(priority))
            except ValueError:
                pass

        category_id = self.request.GET.get("category")
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        assigned_to = self.request.GET.get("assigned_to")
        if assigned_to:
            queryset = queryset.filter(assigned_to_id=assigned_to)

        show_overdue = self.request.GET.get("overdue")
        if show_overdue == "true":
            from django.utils import timezone

            queryset = queryset.filter(
                deadline__lt=timezone.now().date(),
                status__in=[Task.Status.TODO.value, Task.Status.IN_PROGRESS.value],
            )

        ordering = self.request.GET.get("ordering", "-created_at")
        allowed_orderings = [
            "-created_at",
            "created_at",
            "-deadline",
            "deadline",
            "-priority",
            "priority",
        ]
        if ordering not in allowed_orderings:
            ordering = "-created_at"

        return queryset.order_by(ordering)

    def get_context_data(self, **kwargs):
        """Добавляет данные для фильтров, команд и формы списка."""
        context = super().get_context_data(**kwargs)
        user = self.request.user
        team_id = self.kwargs.get("team_id")

        current_team = None
        if team_id:
            try:
                team = Team.objects.get(pk=team_id)
                if TeamMember.objects.filter(team=team, user=user).exists():
                    current_team = team
            except Team.DoesNotExist:
                pass
        context["current_team"] = current_team

        context["task_status_choices"] = Task.Status.choices
        context["task_priority_choices"] = Task.Priority.choices

        if current_team:
            # Контекст командного раздела.
            context["all_categories"] = TaskCategory.objects.filter(team=current_team)
            context["team_members"] = User.objects.filter(
                team_memberships__team=current_team
            ).distinct()
        else:
            # Контекст общего личного раздела.
            user_teams = TeamMember.objects.filter(user=user).values_list(
                "team", flat=True
            )
            context["all_categories"] = (
                TaskCategory.objects.filter(Q(user=user) | Q(team__in=user_teams))
                .distinct()
                .order_by("name")
            )
            context["team_members"] = User.objects.filter(
                team_memberships__team__in=user_teams
            ).distinct()

        context["user_teams"] = Team.objects.filter(members__user=user).distinct()

        return context


class TaskCreateView(
    TaskMixin, TeamAdminAccessMixin,
    FormContextMixin, CreateView,
    OwnershipMixin
):
    """Создаёт личную или командную задачу."""
    form_class = TaskForm
    form_type = "task"
    template_name = "core/form.html"

    def form_valid(self, form):
        self.assign_ownership(form.instance)
        return super().form_valid(form)


class TaskDetailView(TaskMixin, TeamMemberAccessMixin, DetailView):
    """Показывает подробную информацию о задаче."""
    template_name = "tasks/task_detail.html"
    context_object_name = "task"


class TaskUpdateView(
    TaskMixin, TeamAdminAccessMixin, UserTeamObjectQuerysetMixin,
    FormContextMixin, UpdateView
):
    """Редактирует личную или командную задачу."""
    form_class = TaskForm
    form_type = "task"
    template_name = "core/form.html"

    def get_object(self, queryset=None):
        """Проверяет соответствие задачи текущему разделу."""
        obj = super().get_object(queryset)
        team_id = self.kwargs.get("team_id")

        if team_id:
            if obj.team_id != int(team_id):
                raise Http404()
        else:
            if obj.team is not None:
                raise Http404()

        return obj


class TaskDeleteView(
    TeamAdminAccessMixin,
    UserTeamObjectQuerysetMixin,
    DeleteContextMixin,
    DeleteView,
):
    """Удаляет задачу с подтверждением действия."""
    model = Task
    template_name = "core/confirm_delete.html"
    delete_type = "task"
    success_url = reverse_lazy("tasks:task_list")


class TaskCategoryListView(TeamMemberAccessMixin, ListView):
    """Показывает список категорий задач."""
    model = TaskCategory
    template_name = "tasks/task_category_list.html"
    context_object_name = "categories"

    def get_queryset(self):
        user = self.request.user
        team_id = self.kwargs.get("team_id")

        if team_id:
            return TaskCategory.objects.filter(team_id=team_id).order_by("name")
        else:
            user_teams = TeamMember.objects.filter(user=user).values_list(
                "team", flat=True
            )
            return (
                TaskCategory.objects.filter(Q(user=user) | Q(team__in=user_teams))
                .distinct()
                .order_by("name")
            )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team_id = self.kwargs.get("team_id")
        context["current_team"] = Team.objects.get(id=team_id) if team_id else None
        return context


class TaskCategoryCreateView(
    TeamAdminAccessMixin, FormContextMixin,
    CreateView, OwnershipMixin
):
    """Создаёт категорию задач для пользователя или команды."""
    model = TaskCategory
    form_class = TaskCategoryForm
    form_type = "tasks_category"
    template_name = "core/form.html"

    def form_valid(self, form):
        self.assign_ownership(form.instance)
        return super().form_valid(form)


class TaskCategoryUpdateView(
    TeamAdminAccessMixin, FormContextMixin, UserTeamObjectQuerysetMixin, UpdateView
):
    """Редактирует категорию задач для пользователя или команды."""
    model = TaskCategory
    form_class = TaskCategoryForm
    form_type = "tasks_category"
    template_name = "core/form.html"


class TaskCategoryDeleteView(
    TeamAdminAccessMixin, DeleteContextMixin, UserTeamObjectQuerysetMixin, DeleteView
):
    """Удаляет категорию задач с подтверждением действия."""
    model = TaskCategory
    template_name = "core/confirm_delete.html"
    delete_type = "task_category"
    success_url = reverse_lazy("tasks:category_list")


# ====================== ДЕЙСТВИЯ ======================
class TaskMarkAsDoneView(TeamAdminAccessMixin, UpdateView):
    """Отмечает задачу как выполненную."""
    model = Task
    fields = []
    http_method_names = ["post"]

    def form_valid(self, form):
        """Сохраняет статус выполненной задачи."""
        self.object.status = "done"
        self.object.save()
        return super().form_valid(form)

    def get_success_url(self):
        """Возвращает пользователя на страницу задачи."""
        return reverse("tasks:task_detail", kwargs={"pk": self.object.pk})
