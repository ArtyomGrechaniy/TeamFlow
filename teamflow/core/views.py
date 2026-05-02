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

from .constants import COLORS
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
        base_filter = Q(user=user) | Q(team__in=user_teams)

        tasks = Task.objects.filter(base_filter)

        tasks_stats = tasks.aggregate(
            total = Count('id'),
            todo = Count('id', filter=Q(status=TODO_STATUS)),
            in_progress = Count('id', filter=Q(status=IN_PROGRESS_STATUS)),
            done = Count('id', filter=Q(status=DONE_STATUS)),
            archived = Count('id', filter=Q(status=ARCHIVED_STATUS)),
            low_priority = Count('id', filter=Q(priority=LOW_PRIORITY)),
            medium_priority = Count('id', filter=Q(priority=MEDIUM_PRIORITY)),
            high_priority = Count('id', filter=Q(priority=HIGH_PRIORITY)),
            urgent_priority = Count('id', filter=Q(priority=URGENT_PRIORITY)),
            overdue_count = Count('id', filter=Q(deadline__lt=today, status__in=[TODO_STATUS, IN_PROGRESS_STATUS])),
            category_count = Count('category', distinct=True, filter=Q(category__isnull=False))
        )
        total_tasks = tasks_stats['total']
        context['total_tasks_count'] = total_tasks

        context['tasks_todo_count'] = tasks_stats['todo']
        context['tasks_in_progress_count'] = tasks_stats['in_progress']
        context['tasks_done_count'] = tasks_stats['done']
        context['tasks_archived_count'] = tasks_stats['archived']
        
        if total_tasks:
            for key in ['todo', 'in_progress', 'done', 'archived']:
                context[f'tasks_{key}_percent'] = int(context[f'tasks_{key}_count'] / total_tasks * 100)

        else:
            for key in ['todo', 'in_progress', 'done', 'archived']:
                context[f'tasks_{key}_percent'] = 0

        context['tasks_low_priority'] = tasks_stats['low_priority']
        context['tasks_medium_priority'] = tasks_stats['medium_priority']
        context['tasks_high_priority'] = tasks_stats['high_priority']
        context['tasks_urgent_priority'] = tasks_stats['urgent_priority']

        context['overdue_tasks_count'] = tasks_stats['overdue_count']

        context['completed_tasks_count'] = tasks_stats['done']
        

        context['completed_tasks_percent'] = round(
            tasks_stats['done'] / total_tasks * 100 
            if total_tasks else 0
        )

        
        expenses = Expense.objects.filter(base_filter)
        
        expenses_stats = expenses.aggregate(
            total_amount = Sum('amount_rub'),
            total_count = Count('id'),
            category_count = Count('category', distinct=True)
        )

        context['total_expenses_amount'] = expenses_stats['total_amount']
        context['total_expenses_count'] = expenses_stats['total_count']
        
        context['categories_count'] = expenses_stats['category_count'] + tasks_stats['category_count']
        
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
            item['percent'] = str(item['percent']).replace(',', '.')
            item['color'] = COLORS[i % len(COLORS)]

        if rest_total > 0:
            top_10.append({
                'category__name': 'Остальные',
                'total': rest_total,
                'percent': round((rest_total / total * 100), 1) if total else 0
            })

        context['by_category'] = top_10
        
        context['user_teams'] = TeamMember.objects.filter(user=user).select_related('team').annotate(
            count=Count('team'),
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
