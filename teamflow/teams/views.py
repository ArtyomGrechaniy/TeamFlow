from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy

from .forms import TeamForm
from .models import Team, TeamMember
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.views import View
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum
from core.mixins import FormContextMixin
from tasks.models import Task


User = get_user_model()

today = timezone.now().date()


class TeamJoinView(LoginRequiredMixin, View):
    def get(self, request):
        invite_code = request.GET.get('invite_code')

        if not invite_code:
            return redirect('teams:team_list')
        
        try:
            team = Team.objects.get(invite_code=invite_code)
        except Team.DoesNotExist:
            messages.error(request, 'Команда с таким кодом не найдена')
            return redirect('teams:team_list')
        
        TeamMember.objects.get_or_create(
            team=team,
            user=request.user,
            defaults={'role': 'member'}
        )

        messages.success(request, f'Вы успешно присоединились к команде "{team.name}"')
        return redirect('teams:team_detail', pk=team.pk)


class TeamLeaveView(LoginRequiredMixin, View):
    def get(self, request, pk):
        team = get_object_or_404(Team, pk=pk)
        user = request.user

        try:
            membership = TeamMember.objects.get(team=team, user=user)
        except TeamMember.DoesNotExist:
            messages.error(request, 'Вы не состоите в этой команде.')
            return redirect('teams:team_list')

        if membership.role == 'owner':
            messages.error(request, 'Владелец команды не может выйти. Удалите команду или передайте владение.')
            return redirect('teams:team_detail', pk=team.pk)

        membership.delete()

        messages.success(request, f'Вы вышли из команды "{team.name}".')
        return redirect('teams:team_list')


class TeamListView(LoginRequiredMixin, ListView):
    model = Team
    template_name = 'teams/team_list.html'
    context_object_name = 'teams'

    def get_queryset(self):
        user = self.request.user
        return Team.objects.filter(members__user=user).distinct().order_by('-created_at')
    

class TeamCreateView(LoginRequiredMixin, FormContextMixin, CreateView):
    model = Team
    form_class = TeamForm
    template_name = 'core/form.html'
    form_type = 'team'
    success_url = reverse_lazy('teams:team_list')

    def form_valid(self, form):
        form.instance.owner = self.request.userBan
        response = super().form_valid(form)

        TeamMember.objects.create(
            team=self.object,
            user=self.request.user,
            role='owner'
        )
        return response


class TeamDetailView(LoginRequiredMixin, DetailView):
    model = Team
    template_name = 'teams/team_detail.html'
    context_object_name = 'team'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = self.object
        user = self.request.user

        try:
            membership = TeamMember.objects.get(team=team, user=user)
            context['user_role'] = membership.role
            context['is_owner'] = membership.role == 'owner'
            context['is_admin'] = membership.role in ['owner', 'admin']
        except TeamMember.DoesNotExist:
            context['user_role'] = None
            context['is_owner'] = False
            context['is_admin'] = False
        
        context['members'] = TeamMember.objects.filter(team=team).select_related('user', 'user__profile')
        context['archived_tasks'] = team.tasks.filter(status=Task.Status.ARCHIVED).count()
        context['active_tasks'] = team.tasks.filter(status__in=[Task.Status.TODO, Task.Status.IN_PROGRESS]).order_by('-priority', '-deadline')
        context['active_tasks_count'] = context['active_tasks'].count
        context['overdue_tasks_count'] = team.tasks.filter(status__in=[Task.Status.TODO, Task.Status.IN_PROGRESS], deadline__lt=today).count()
        
        start_date_last_month = today - timedelta(days=30)
        expenses_last_month = team.expenses.filter(
            date__gte=start_date_last_month
            ).select_related('category'
        ).order_by('-date', '-amount_rub')

        context['expenses_last_month'] = expenses_last_month
        context['expenses_last_month_count'] = expenses_last_month.count()
        context['expenses_last_month_total'] = expenses_last_month.aggregate(
            Sum('amount_rub')
        )['amount_rub__sum'] or 0
        
        start_date_last_year = today - timedelta(days=365)
        expenses_last_year = team.expenses.filter(
            date__gte=start_date_last_year
        ).order_by('-date', '-amount_rub')

        context['expenses_last_year'] = expenses_last_year
        context['expenses_last_year_count'] = expenses_last_year.count()
        context['expenses_last_year_total'] = expenses_last_year.aggregate(
            Sum('amount_rub')
        )['amount_rub__sum'] or 0

        
        
        return context


class TeamUpdateView(LoginRequiredMixin, UpdateView):
    model = Team
    form_class = TeamForm
    template_name = 'core/form.html'
    form_type = 'team'

    def get_success_url(self):
        return reverse_lazy('teams:team_detail', kwargs={'pk': self.object.pk})

    def get_queryset(self):
        return Team.objects.filter(owner=self.request.user)


class TeamDeleteView(LoginRequiredMixin, DeleteView):
    model = Team
    template_name = 'core/confirm_delete.html'
    delete_type = 'team'
    success_url = reverse_lazy('teams:team_list')

    def get_queryset(self):
        return Team.objects.filter(owner=self.request.user)
    

class TeamMemberListView(LoginRequiredMixin, DetailView):
    model = Team
    template_name = 'teams/team_member_list.html'
    context_object_name = 'team'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = self.object
        user = self.request.user

        try:
            membership = TeamMember.objects.get(team=team, user=user)
            context['is_owner'] = membership.role == 'owner'
            context['is_admin'] = membership.role in ['owner', 'admin']
        except TeamMember.DoesNotExist:
            context['is_owner'] = False
            context['is_admin'] = False

        context['members'] = TeamMember.objects.filter(team=team).select_related('user')

        return context



class TeamMemberKickView(LoginRequiredMixin, View):
    def post(self, request, pk, user_id):
        team = get_object_or_404(Team, pk=pk)
        current_user = request.user
        target_user = get_object_or_404(User, pk=user_id)

        try:
            current_membership = TeamMember.objects.get(team=team, user=current_user)
        except TeamMember.DoesNotExist:
            messages.error(request, 'Вы не состоите в этой команде.')
            return redirect('teams:team_detail', pk=team.pk)

        if current_membership.role not in ['owner', 'admin']:
            messages.error(request, 'У вас нет прав на исключение участников.')
            return redirect('teams:team_detail', pk=team.pk)

        if target_user == team.owner:
            messages.error(request, 'Нельзя исключить владельца команды.')
            return redirect('teams:team_member_list', pk=team.pk)

        TeamMember.objects.filter(team=team, user=target_user).delete()

        messages.success(
            request, f'Пользователь {target_user.get_full_name() or target_user.username} исключён из команды.'
        )
        return redirect('teams:team_member_list', pk=team.pk)
    

class TeamMemberRoleChangeView(LoginRequiredMixin, View):
    def post(self, request, pk, user_id):
        team = get_object_or_404(Team, pk=pk)
        target_user = get_object_or_404(User, pk=user_id)
        new_role = request.POST.get('role')

        if team.owner != request.user:
            messages.error(request, 'Только владелец команды может менять роли.')
            return redirect('teams:team_member_list', pk=team.pk)

        try:
            membership = TeamMember.objects.get(team=team, user=target_user)
            membership.role = new_role
            membership.save()

            messages.success(request, f'Роль пользователя {target_user.username} изменена на {new_role}.')
        except TeamMember.DoesNotExist:
            messages.error(request, 'Пользователь не состоит в команде.')

        return redirect('teams:team_member_list', pk=team.pk)