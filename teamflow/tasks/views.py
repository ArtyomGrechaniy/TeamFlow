from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.db.models import Q

from core.mixins import FormContextMixin, TeamAdminCreateAccessMixin, TeamMemberAccessMixin, TeamAdminAccessMixin, TeamListAccessMixin, DeleteContextMixin
from .models import Task, TaskCategory
from .forms import TaskForm, TaskCategoryForm
from teams.models import Team, TeamMember
from django.contrib.auth import get_user_model

User = get_user_model()


class TaskMixin(LoginRequiredMixin):
    model = Task
    success_url = reverse_lazy('tasks:task_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        if getattr(self, 'object', None) and self.object.team_id:
            kwargs['team_id'] = self.object.team_id
        else:
            kwargs['user'] = self.request.user

        return kwargs


class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'tasks/task_list.html'
    context_object_name = 'tasks'
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        team_id = self.kwargs.get('team_id')
        queryset = Task.objects.all().select_related('category', 'team', 'assigned_to')

        if team_id:
            queryset = queryset.filter(team_id=team_id)
        else:
            user_teams = TeamMember.objects.filter(user=user).values_list('team', flat=True)
            queryset = queryset.filter(Q(user=user) | Q(team__in=user_teams))

        status = self.request.GET.get('status')
        if status:
            try:
                queryset = queryset.filter(status=int(status))
            except ValueError:
                pass

        priority = self.request.GET.get('priority')
        if priority:
            try:
                queryset = queryset.filter(priority=int(priority))
            except ValueError:
                pass

        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        assigned_to = self.request.GET.get('assigned_to')
        if assigned_to:
            queryset = queryset.filter(assigned_to_id=assigned_to)

        show_overdue = self.request.GET.get('overdue')
        if show_overdue == 'true':
            from django.utils import timezone
            queryset = queryset.filter(
                deadline__lt=timezone.now().date(),
                status__in=[Task.Status.TODO.value, Task.Status.IN_PROGRESS.value]
            )

        ordering = self.request.GET.get('ordering', '-created_at')
        allowed_orderings = ['-created_at', 'created_at', '-deadline', 'deadline', '-priority', 'priority']
        if ordering not in allowed_orderings:
            ordering = '-created_at'

        return queryset.order_by(ordering)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        team_id = self.kwargs.get('team_id')

        current_team = None
        if team_id:
            try:
                team = Team.objects.get(pk=team_id)
                if TeamMember.objects.filter(team=team, user=user).exists():
                    current_team = team
            except Team.DoesNotExist:
                pass
        context['current_team'] = current_team

        context['task_status_choices'] = Task.Status.choices
        context['task_priority_choices'] = Task.Priority.choices

        if current_team:
            context['all_categories'] = TaskCategory.objects.filter(team=current_team)
            context['team_members'] = User.objects.filter(team_memberships__team=current_team).distinct()
        else:
            user_teams = TeamMember.objects.filter(user=user).values_list('team', flat=True)
            context['all_categories'] = TaskCategory.objects.filter(
                Q(user=user) | Q(team__in=user_teams)
            ).distinct().order_by('name')
            context['team_members'] = User.objects.filter(
                team_memberships__team__in=user_teams
            ).distinct()

        context['user_teams'] = Team.objects.filter(members__user=user).distinct()

        return context


class TaskCreateView(
    TaskMixin,
    TeamAdminCreateAccessMixin,
    FormContextMixin,
    CreateView
):
    form_class = TaskForm
    form_type = 'task'
    template_name = 'core/form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        team_id = self.kwargs.get('team_id')
        if team_id:
            kwargs['team_id'] = self.kwargs.get('team_id')
        else:
            kwargs['user'] = self.request.user
        
        return kwargs


class TaskDetailView(
    TaskMixin,
    TeamMemberAccessMixin,
    DetailView
):
    template_name = 'tasks/task_detail.html'
    context_object_name = 'task'


class TaskUpdateView(
    TaskMixin,
    TeamAdminAccessMixin,
    FormContextMixin,
    UpdateView
):
    form_class = TaskForm
    form_type = 'task'
    template_name = 'core/form.html'


class TaskDeleteView(
    LoginRequiredMixin,
    TeamAdminAccessMixin,
    DeleteContextMixin,
    DeleteView
):
    model = Task
    template_name = 'core/confirm_delete.html'
    delete_type = 'task'
    success_url = reverse_lazy('tasks:task_list')


class TaskCategoryListView(LoginRequiredMixin, ListView):
    model = TaskCategory
    template_name = 'tasks/task_category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        user = self.request.user
        team_id = self.kwargs.get('team_id')

        if team_id:
            return TaskCategory.objects.filter(team_id=team_id).order_by('name')
        else:
            user_teams = TeamMember.objects.filter(user=user).values_list('team', flat=True)
            return TaskCategory.objects.filter(
                Q(user=user) | Q(team__in=user_teams)
            ).distinct().order_by('name')


class TaskCategoryCreateView(
    LoginRequiredMixin,
    TeamAdminCreateAccessMixin,
    FormContextMixin,
    CreateView
):
    model = TaskCategory
    form_class = TaskCategoryForm
    form_type = 'tasks_category'
    template_name = 'core/form.html'

    def form_valid(self, form):
        team_id = self.kwargs.get('team_id')
        if team_id:
            form.instance.team_id = team_id
            form.instance.user = None
        else:
            form.instance.user = self.request.user
            form.instance.team = None

        return super().form_valid(form)
    

class TaskCategoryDeleteView(
    LoginRequiredMixin,
    TeamAdminAccessMixin,
    DeleteContextMixin,
    DeleteView
):
    model = TaskCategory
    template_name = 'core/confirm_delete.html'
    form_type = 'tasks_category'
    success_url = reverse_lazy('tasks:task_category_list')


class TaskMarkAsDoneView(LoginRequiredMixin, TeamAdminAccessMixin, UpdateView):
    model = Task
    fields = []
    http_method_names = ['post']

    def form_valid(self, form):
        self.object.status = 'done'
        self.object.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('tasks:task_detail', kwargs={'pk': self.object.pk})