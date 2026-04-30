from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin, LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import Http404
from django.core.exceptions import PermissionDenied

from teams.models import TeamMember


class OnlyAuthorAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        object = self.get_object()
        return object.user == self.request.user
    

class OwnershipMixin:
    def get_team_id(self):
        return self.kwargs.get('team_id')

    def assign_ownership(self, instance):
        team_id = self.get_team_id()
        
        instance.team_id = team_id if team_id else None
        instance.user = self.request.user if not team_id else None

        return instance


class TeamAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    required_roles = None

    def get_team_id(self):
        return self.kwargs.get('team_id')

    def has_team_access(self, user, team_id, roles=None):
        qs = TeamMember.objects.filter(user=user, team_id=team_id)

        if roles:
            qs = qs.filter(role__in=roles)
        
        return qs.exists()
    
    def test_func(self):
        if self.get_team_id():
            return self.has_team_access(
                self.request.user,
                self.get_team_id(),
                self.required_roles
            )
        else:
            return True

    def handle_no_permission(self):
        raise Http404()


class TeamMemberAccessMixin(TeamAccessMixin):
    pass


class TeamAdminAccessMixin(TeamAccessMixin):
    required_roles = ['admin', 'owner']
    

class TeamOwnerAccessMixin(TeamAccessMixin):
    required_roles = ['owner',]


class FormContextMixin:

    form_type = None

    FORM_CONTEXTS = {
        'expense': {
            'icon': '💸',
            'header_color': 'bg-primary',
            'button_color': 'btn-primary',
            'cancel_url': reverse_lazy('expenses:expense_list'),
            'create_title': 'Новый расход',
            'edit_title': 'Редактировать расход',
            'create_submit': 'Добавить расход',
            'edit_submit': 'Сохранить изменения',
        },
        'task': {
            'icon': '✅',
            'header_color': 'bg-success',
            'button_color': 'btn-success',
            'cancel_url': reverse_lazy('tasks:task_list'),
            'create_title': 'Новая задача',
            'edit_title': 'Редактировать задачу',
            'create_submit': 'Создать задачу',
            'edit_submit': 'Сохранить изменения',
        },
        'expenses_category': {
            'icon': '🏷️',
            'header_color': 'bg-info',
            'button_color': 'btn-info',
            'cancel_url': reverse_lazy('expenses:category_list'),
            'create_title': 'Новая категория расходов',
            'edit_title': 'Редактировать категорию расходов',
            'create_submit': 'Создать категорию',
            'edit_submit': 'Сохранить изменения',
        },
        'tasks_category': {
            'icon': '🏷️',
            'header_color': 'bg-info',
            'button_color': 'btn-info',
            'cancel_url': reverse_lazy('tasks:category_list'),
            'create_title': 'Новая категория задач',
            'edit_title': 'Редактировать категорию задач',
            'create_submit': 'Создать категорию',
            'edit_submit': 'Сохранить изменения',
        },
        'team': {
            'icon': '👥',
            'header_color': 'bg-primary',
            'button_color': 'btn-primary',
            'cancel_url': reverse_lazy('teams:team_list'),
            'create_title': 'Новая команда',
            'edit_title': 'Редактировать команду',
            'create_submit': 'Создать команду',
            'edit_submit': 'Сохранить изменения',
        },
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if not self.form_type:
            return context

        config = self.FORM_CONTEXTS.get(self.form_type)
        if not config:
            return context

        is_create = not getattr(self, 'object', None)
        team_id = self.kwargs.get('team_id')

        if team_id:
            if self.form_type == 'task':
                cancel_url = reverse_lazy('teams:tasks:task_list', kwargs={'team_id': team_id})
            elif self.form_type == 'tasks_category':
                cancel_url = reverse_lazy('teams:tasks:category_list', kwargs={'team_id': team_id})
            elif self.form_type == 'expense':
                cancel_url = reverse_lazy('teams:expenses:expense_list', kwargs={'team_id': team_id})
            elif self.form_type == 'expenses_category':
                cancel_url = reverse_lazy('teams:expenses:category_list', kwargs={'team_id': team_id})
            else:
                cancel_url = config['cancel_url']
        else:
            cancel_url = config['cancel_url']

        context.update({
            'title': config['create_title'] if is_create else config['edit_title'],
            'icon': config['icon'],
            'header_color': config['header_color'],
            'button_color': config['button_color'],
            'submit_text': config['create_submit'] if is_create else config['edit_submit'],
            'cancel_url': cancel_url,
        })

        return context
    
    def get_success_url(self):
        team_id = self.kwargs.get('team_id')

        if self.form_type == 'task':
            if team_id:
                return reverse_lazy('teams:tasks:task_list', kwargs={'team_id': team_id})
            return reverse_lazy('tasks:task_list')

        elif self.form_type == 'task_category':
            if team_id:
                return reverse_lazy('teams:tasks:category_list', kwargs={'team_id': team_id})
            return reverse_lazy('tasks:task_category_list')

        elif self.form_type == 'expense':
            if team_id:
                return reverse_lazy('teams:expenses:expense_list', kwargs={'team_id': team_id})
            return reverse_lazy('expenses:expense_list')

        elif self.form_type == 'expenses_category':
            if team_id:
                return reverse_lazy('team:expenses:category_list', kwargs={'team_id': team_id})
            return reverse_lazy('expenses:category_list')

        elif self.form_type == 'team':
            return reverse_lazy('teams:team_list')

        return reverse_lazy('core:home')
    

class DeleteContextMixin:
    delete_type = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team_id = self.kwargs.get('team_id')

        if self.delete_type == 'expense':
            context.update({
                'title': 'Удаление расхода',
                'message': 'Вы уверены, что хотите удалить этот расход?',
                'icon': '💸',
                'cancel_url': reverse_lazy('expenses:expense_list') if not team_id else reverse_lazy('teams:expenses:expense_list', kwargs={'team_id': team_id}),
            })

        elif self.delete_type == 'task':
            context.update({
                'title': 'Удаление задачи',
                'message': 'Вы уверены, что хотите удалить эту задачу?',
                'icon': '✅',
                'cancel_url': reverse_lazy('tasks:task_list') if not team_id else reverse_lazy('teams:tasks:task_list', kwargs={'team_id': team_id}),
            })

        elif self.delete_type == 'expense_category':
            context.update({
                'title': 'Удаление категории расходов',
                'message': 'Вы уверены, что хотите удалить эту категорию?',
                'icon': '🏷️',
                'cancel_url': reverse_lazy('expenses:category_list') if not team_id else reverse_lazy('teams:expenses:category_list', kwargs={'team_id': team_id}),
            })

        elif self.delete_type == 'task_category':
            context.update({
                'title': 'Удаление категории задач',
                'message': 'Вы уверены, что хотите удалить эту категорию задач?',
                'icon': '🏷️',
                'cancel_url': reverse_lazy('tasks:task_category_list') if not team_id else reverse_lazy('teams:tasks:category_list', kwargs={'team_id': team_id}),
            })

        elif self.delete_type == 'team':
            context.update({
                'title': 'Удаление команды',
                'message': 'Вы уверены, что хотите удалить эту команду? Все расходы и задачи внутри будут удалены!',
                'icon': '👥',
                'cancel_url': reverse_lazy('teams:team_list'),
            })

        return context

    def get_success_url(self):
        team_id = self.kwargs.get('team_id')

        if self.delete_type == 'expense':
            return reverse_lazy('teams:expenses:expense_list', kwargs={'team_id': team_id}) if team_id else reverse_lazy('expenses:expense_list')

        elif self.delete_type == 'task':
            return reverse_lazy('teams:tasks:task_list', kwargs={'team_id': team_id}) if team_id else reverse_lazy('tasks:task_list')

        elif self.delete_type == 'expense_category':
            return reverse_lazy('teams:expenses:category_list', kwargs={'team_id': team_id}) if team_id else reverse_lazy('expenses:category_list')

        elif self.delete_type == 'task_category':
            return reverse_lazy('teams:tasks:category_list', kwargs={'team_id': team_id}) if team_id else reverse_lazy('tasks:task_category_list')

        elif self.delete_type == 'team':
            return reverse_lazy('teams:team_list')

        return reverse_lazy('core:home')