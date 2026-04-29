from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Sum, Q
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (CreateView, DeleteView, ListView,
                                  TemplateView, UpdateView, DetailView)
from django.http import Http404

from core.constants import NO_CATEGORY, OTHER_LABEL

from .forms import ExpenseCategoryForm, ExpenseForm
from .models import Expense, ExpenseCategory
from teams.models import Team, TeamMember
from core.mixins import (FormContextMixin, TeamAdminCreateAccessMixin, 
                         TeamMemberAccessMixin, TeamAdminAccessMixin, 
                         TeamListAccessMixin, DeleteContextMixin)


# ====================== МИКСИНЫ ======================
class ExpenseMixin(LoginRequiredMixin):
    model = Expense
    success_url = reverse_lazy('expenses:expense_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        if getattr(self, 'object', None) and self.object.team_id:
            kwargs['team_id'] = self.object.team_id
        else:
            kwargs['user'] = self.request.user

        return kwargs



# ====================== CRUD ======================
class ExpenseCreateView(
    TeamAdminCreateAccessMixin,
    ExpenseMixin,
    FormContextMixin,
    CreateView
):
    form_class = ExpenseForm
    template_name = 'core/form.html'
    form_type = 'expense'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        team_id = self.kwargs.get('team_id')
        if team_id:
            kwargs['team_id'] = self.kwargs.get('team_id')
        else:
            kwargs['user'] = self.request.user
        
        return kwargs


class ExpenseUpdateView(
    TeamAdminAccessMixin,
    ExpenseMixin,
    FormContextMixin,
    UpdateView
):
    form_class = ExpenseForm
    form_type = 'expense'
    template_name = 'core/form.html'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        team_id = self.kwargs.get('team_id')

        if team_id:
            if obj.team_id != int(team_id):
                raise Http404()
        else:
            if obj.team is not None:
                raise Http404()

        return obj

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        team_id = self.kwargs.get('team_id')

        if team_id:
            kwargs['team_id'] = team_id
        else:
            kwargs['user'] = self.request.user

        return kwargs


class ExpenseDeleteView(
    LoginRequiredMixin,
    TeamAdminAccessMixin,
    DeleteContextMixin,
    DeleteView
):
    model = Expense
    template_name = 'core/confirm_delete.html'
    delete_type = 'expense'
    success_url = reverse_lazy('expenses:expense_list')

    def get_object(self, queryset = None):
        obj = super().get_object(queryset)
        team_id = self.kwargs.get('team_id')
        
        if team_id:
            if obj.team_id != int(team_id):
                raise Http404()
        else:
            if obj.team is not None:
                raise Http404()
        
        return obj


class ExpenseCategoryCreateView(
    TeamAdminCreateAccessMixin,
    LoginRequiredMixin,
    FormContextMixin,
    CreateView
):
    model = ExpenseCategory
    form_class = ExpenseCategoryForm
    form_type = 'expenses_category'
    template_name = 'core/form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        team_id = self.kwargs.get('team_id')

        if team_id:
            kwargs['team_id'] = team_id
        else:
            kwargs['user'] = self.request.user

        return kwargs

    def form_valid(self, form):
        team_id = self.kwargs.get('team_id')
        if team_id:
            form.instance.team_id = team_id
            form.instance.user = None
        else:
            form.instance.user = self.request.user
            form.instance.team = None
        return super().form_valid(form)
    
    def get_success_url(self):
        team_id = self.kwargs.get('team_id')
        if team_id:
            return reverse_lazy('teams:expenses:category_list', kwargs={'team_id': team_id})
        else:
            return reverse_lazy('expenses:category_list')
        

class ExpenseCategoryUpdateView(
    LoginRequiredMixin,
    TeamAdminAccessMixin,
    FormContextMixin,
    UpdateView
):
    model = ExpenseCategory
    form_class = ExpenseCategoryForm
    form_type = 'expenses_category'
    template_name = 'core/form.html'

    def get_success_url(self):
        return reverse_lazy('expenses:category_list')

    def get_queryset(self):
        user = self.request.user
        user_teams = TeamMember.objects.filter(
            user=user, 
            role__in=['owner', 'admin']
        ).values_list('team', flat=True)

        return ExpenseCategory.objects.filter(
            Q(user=user) | Q(team__in=user_teams)
        )



class ExpenseCategoryDeleteView(TeamAdminAccessMixin, DeleteView):
    model = ExpenseCategory
    success_url = reverse_lazy('expenses:category_list')

    def get_queryset(self):
        return ExpenseCategory.objects.filter(user=self.request.user)


class ExpenseDetailView(ExpenseMixin, TeamMemberAccessMixin, DetailView):
    template_name = 'expenses/expense_detail.html'
    context_object_name = 'expense'


class ExpenseListView(LoginRequiredMixin, TeamListAccessMixin, ListView):
    model = Expense
    template_name = 'expenses/expense_list.html'
    context_object_name = 'expenses'
    paginate_by = 20

    def get_base_queryset(self):
        user = self.request.user
        team_id = self.kwargs.get('team_id')

        if team_id:
            return Expense.objects.filter(team_id=team_id)
        else:
            user_teams = TeamMember.objects.filter(user=user).values_list('team', flat=True)
            return Expense.objects.filter(
                Q(user=user) | Q(team__in=user_teams)
            )

    def get_queryset(self):
        queryset = self.get_base_queryset().select_related('category', 'team')

        selected_categories = self.request.GET.getlist('category')
        if selected_categories:
            queryset = queryset.filter(category__id__in=selected_categories)

        return queryset.order_by('-date', '-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        team_id = self.kwargs.get('team_id')

        if team_id:
            context['current_team'] = Team.objects.get(id=team_id)
            context['user_teams'] = None
            context['all_categories'] = ExpenseCategory.objects.filter(team_id=team_id)
            context['has_any_expenses'] = Expense.objects.filter(team_id=team_id).exists()
            context['selected_categories'] = []
        else:
            context['current_team'] = None
            context['user_teams'] = Team.objects.filter(members__user=user).distinct()

            context['all_categories'] = ExpenseCategory.objects.filter(
                Q(user=user) |
                Q(team__in=TeamMember.objects.filter(user=user).values_list('team', flat=True))
            ).distinct().order_by('name')

            user_teams = TeamMember.objects.filter(user=user).values_list('team', flat=True)
            context['has_any_expenses'] = Expense.objects.filter(
                Q(user=user) | Q(team__in=user_teams)
            ).exists()

            context['selected_categories'] = self.request.GET.getlist('category')

        return context


class ExpenseCategoryListView(TeamListAccessMixin, ListView):
    model = ExpenseCategory
    template_name = 'expenses/expense_category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.annotate(
            expense_count=Count('expenses'),
            total_amount=Sum('expenses__amount_rub')
        ).order_by('name')


class StatisticsView(ExpenseMixin, TemplateView):
    template_name = 'expenses/statistics.html'
    
    TOP_CATEGORIES = 10
    TOP_EXPENSES = 5

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        expenses = self.get_queryset()

        context['total_all_time'] = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
        context['total_this_month'] = expenses.filter(
            date__month=timezone.now().month,
            date__year=timezone.now().year
        ).aggregate(Sum('amount'))['amount__sum'] or 0

        by_category_qs = (
            expenses.values('category__name')
            .annotate(total=Sum('amount'))
            .order_by('-total')
        )
        
        by_category_list = list(by_category_qs)

        top_10 = by_category_list[:self.TOP_CATEGORIES]
        rest = by_category_list[self.TOP_CATEGORIES:]

        rest_total = sum(item['total'] for item in rest)

        color_iter = iter(COLORS.values())

        for item in top_10:
            if item['category__name'] is None:
                item['category__name'] = NO_CATEGORY
            item['color'] = next(color_iter, OTHER_COLOR)
        
        if rest_total > 0:
            top_10.append({
                    'category__name': OTHER_LABEL,
                    'total': rest_total,
                    'color': OTHER_COLOR
            })
         
        context['by_category'] = top_10

        total = context['total_all_time']

        for item in context['by_category']:
            item['percentage'] = round((item['total'] / total * 100), 1) if total else 0

        top_expenses = (
            expenses
            .select_related('category')
            .order_by('-amount')[:self.TOP_EXPENSES]
        )

        for expense in top_expenses:
            cat = getattr(expense, 'category', None)
            expense.category_color = getattr(cat, 'color', None) or OTHER_COLOR

        context['top_expenses'] = top_expenses
        return context
