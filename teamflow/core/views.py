from django.contrib.auth import get_user_model, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Count, Q, Sum
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, TemplateView, UpdateView, DetailView

from expenses.models import Expense, ExpenseCategory
from tasks.models import Task, TaskCategory
from teams.models import Team, TeamMember

from .forms import LoginForm, ProfileForm, RegisterForm
from .models import Profile

User = get_user_model()

today = timezone.now().date()

TODO_STATUS = Task.Status.TODO
IN_PROGRESS_STATUS = Task.Status.IN_PROGRESS
DONE_STATUS = Task.Status.DONE
ARCHIVED_STATUS = Task.Status.ARCHIVED

URGENT_PRIORITY = Task.Priority.URGENT
HIGH_PRIORITY = Task.Priority.HIGH
MEDIUM_PRIORITY = Task.Priority.MEDIUM
LOW_PRIORITY = Task.Priority.LOW


class ProfileView(DetailView):
    model = Profile
    template_name = 'profile/profile.html'
    context_object_name = 'profile'
    slug_field = 'user__username'
    slug_url_kwarg = 'username'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_owner'] = self.request.user == self.object.user
        return context


class ProfileStatisticsView(LoginRequiredMixin, TemplateView):
    template_name = 'profile/profile_statistics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        user_teams = TeamMember.objects.filter(user=user).values_list('team', flat=True)
        
        expenses = Expense.objects.filter(
            Q(user=user) | Q(team__in=user_teams)
        )
        
        context['total_expenses_amount'] = expenses.aggregate(
            Sum('amount_rub')
        )['amount_rub__sum'] or 0
        
        context['total_expenses_count'] = expenses.count()

        tasks = Task.objects.filter(
            Q(user=user) | Q(team__in=user_teams)
        )

        total_tasks = tasks.count()
        
        context['total_tasks_count'] = tasks.count()
        context['completed_tasks_count'] = tasks.filter(status=DONE_STATUS).count()
        
        if context['total_tasks_count'] > 0:
            context['completed_tasks_percent'] = round(
                (context['completed_tasks_count'] / context['total_tasks_count']) * 100
            )
        else:
            context['completed_tasks_percent'] = 0

        context['teams_count'] = TeamMember.objects.filter(user=user).count()

        expense_categories = ExpenseCategory.objects.filter(
            Q(user=user) | Q(team__in=user_teams)
        ).count()
        
        task_categories = TaskCategory.objects.filter(
            Q(user=user) | Q(team__in=user_teams)
        ).count()
        
        context['categories_count'] = expense_categories + task_categories
        
        by_category_qs = (
            expenses.values('category__name')
            .annotate(total=Sum('amount_rub'))
            .order_by('-total')
        )

        by_category_list = list(by_category_qs)
        top_10 = by_category_list[:10]
        rest = by_category_list[10:]

        rest_total = sum(item['total'] for item in rest) if rest else 0
        total = context['total_expenses_amount']

        for i, item in enumerate(top_10):
            if item['category__name'] is None:
                item['category__name'] = 'Без категории'
            item['percent'] = round((item['total'] / total * 100), 1) if total else 0

        if rest_total > 0:
            top_10.append({
                'category__name': 'Остальные',
                'total': rest_total,
                'percent': round((rest_total / total * 100), 1) if total else 0
            })

        context['by_category'] = top_10
        
        context['tasks_todo_count'] = tasks.filter(status=TODO_STATUS).count()
        context['tasks_in_progress_count'] = tasks.filter(status=IN_PROGRESS_STATUS).count()
        context['tasks_done_count'] = tasks.filter(status=DONE_STATUS).count()
        context['tasks_archived_count'] = tasks.filter(status=ARCHIVED_STATUS).count()
        
        try:
            context['tasks_todo_percent'] = int(context['tasks_todo_count'] / total_tasks * 100)
            context['tasks_in_progress_percent'] = int(context['tasks_in_progress_count'] / total_tasks * 100)
            context['tasks_done_percent'] = int(context['tasks_done_count'] / total_tasks * 100)
            context['tasks_archived_percent'] = int(context['tasks_archived_count'] / total_tasks * 100)
        except ZeroDivisionError:
            context['tasks_todo_percent'] = 0
            context['tasks_in_progress_percent'] = 0
            context['tasks_done_percent'] = 0
            context['tasks_archived_percent'] = 0

        context['tasks_low_priority'] = tasks.filter(priority=LOW_PRIORITY).count()
        context['tasks_medium_priority'] = tasks.filter(priority=MEDIUM_PRIORITY).count()
        context['tasks_high_priority'] = tasks.filter(priority=HIGH_PRIORITY).count()
        context['tasks_urgent_priority'] = tasks.filter(priority=URGENT_PRIORITY).count()

        context['overdue_tasks_count'] = tasks.filter(
            deadline__lt=timezone.now().date(),
            status__in=[TODO_STATUS, IN_PROGRESS_STATUS]
        ).count()
        
        context['user_teams'] = TeamMember.objects.filter(user=user).select_related('team').annotate(
            tasks_count=Count('team__tasks'),
            expenses_count=Count('team__expenses'),
            overdue_tasks_count=Count(
                'team__tasks',
                filter=Q(
                    team__tasks__deadline__lt=today,
                    team__tasks__status__in=[TODO_STATUS, IN_PROGRESS_STATUS]
                )
            )
        )


        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = Profile
    form_class = ProfileForm
    template_name = 'profile/profile_edit.html'

    def get_object(self, queryset=None):
        return self.request.user.profile

    def get_success_url(self):
        return reverse_lazy('core:profile', kwargs={'username': self.request.user.username})
    
class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = 'registration/register.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response

    def get_success_url(self):
        return reverse('core:profile', kwargs={'username': self.object.username})


class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    redirect_authenticated_user = True
    authentication_form = LoginForm

    def get_success_url(self):
        return reverse_lazy('core:profile', kwargs={'username': self.request.user.username})


class HomeView(TemplateView):
    template_name = 'core/index.html'
