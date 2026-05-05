from math import ceil

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q, Sum, Min, Max
from django.http import Http404
from django.urls import reverse_lazy
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
    OwnershipMixin,
    TeamAdminAccessMixin,
    TeamMemberAccessMixin,
    UserTeamObjectQuerysetMixin
)
from teams.models import Team, TeamMember

from .forms import ExpenseCategoryForm, ExpenseForm
from .models import Expense, ExpenseCategory


# ====================== МИКСИНЫ ======================
class ExpenseMixin(LoginRequiredMixin):
    """Добавляет общие настройки и данные формы для views расходов."""
    model = Expense
    success_url = reverse_lazy("expenses:expense_list")


# ====================== CRUD ======================
class ExpenseCreateView(
    TeamAdminAccessMixin, OwnershipMixin, ExpenseMixin,
    FormContextMixin, CreateView
):    
    """Создаёт командный или личный расход."""
    form_class = ExpenseForm
    template_name = "core/form.html"
    form_type = "expense"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        team_id = self.kwargs.get("team_id")

        if team_id:
            kwargs["team_id"] = team_id
        else:
            kwargs["user"] = self.request.user

        return kwargs

    def form_valid(self, form):
        self.assign_ownership(form.instance)
        return super().form_valid(form)


class ExpenseUpdateView(
    TeamAdminAccessMixin, ExpenseMixin, FormContextMixin,
    UpdateView, UserTeamObjectQuerysetMixin
):
    """Редактирует личный или командный расход."""
    form_class = ExpenseForm
    form_type = "expense"
    template_name = "core/form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        team_id = self.kwargs.get("team_id")

        if team_id:
            kwargs["team_id"] = team_id
        else:
            kwargs["user"] = self.request.user

        return kwargs


class ExpenseDeleteView(
    TeamAdminAccessMixin, DeleteContextMixin,
    DeleteView, UserTeamObjectQuerysetMixin
):
    """Удаляет расход с подтверждением действия."""
    model = Expense
    template_name = "core/confirm_delete.html"
    delete_type = "expense"
    success_url = reverse_lazy("expenses:expense_list")


class ExpenseCategoryCreateView(
    TeamAdminAccessMixin,
    OwnershipMixin,
    LoginRequiredMixin,
    FormContextMixin,
    CreateView,
    UserTeamObjectQuerysetMixin
):
    """Создаёт категорию расходов для пользователя или команды."""
    model = ExpenseCategory
    form_class = ExpenseCategoryForm
    form_type = "expenses_category"
    template_name = "core/form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        team_id = self.kwargs.get("team_id")

        if team_id:
            kwargs["team_id"] = team_id
        else:
            kwargs["user"] = self.request.user

        return kwargs

    def form_valid(self, form):
        self.assign_ownership(form.instance)
        return super().form_valid(form)

    def get_success_url(self):
        team_id = self.kwargs.get("team_id")
        if team_id:
            return reverse_lazy(
                "teams:expenses:category_list", kwargs={"team_id": team_id}
            )
        else:
            return reverse_lazy("expenses:category_list")


class ExpenseCategoryUpdateView(
    TeamAdminAccessMixin, FormContextMixin, UserTeamObjectQuerysetMixin, UpdateView
):
    """Редактирует категорию расходов."""
    model = ExpenseCategory
    form_class = ExpenseCategoryForm
    form_type = "expenses_category"
    template_name = "core/form.html"


class ExpenseCategoryDeleteView(
    TeamAdminAccessMixin, DeleteContextMixin, UserTeamObjectQuerysetMixin, DeleteView
):
    """Удаляет личную категорию расходов."""
    model = ExpenseCategory
    template_name = "core/confirm_delete.html"
    delete_type = "expense_category"
    success_url = reverse_lazy("expenses:category_list")


class ExpenseDetailView(ExpenseMixin, TeamMemberAccessMixin, DetailView):
    template_name = "expenses/expense_detail.html"
    context_object_name = "expense"


class ExpenseListView(TeamMemberAccessMixin, ListView):
    model = Expense
    template_name = "expenses/expense_list.html"
    context_object_name = "expenses"
    paginate_by = 20

    def get_base_queryset(self):
        user = self.request.user
        team_id = self.kwargs.get("team_id")

        if team_id:
            return Expense.objects.filter(team_id=team_id)
        else:
            user_teams = TeamMember.objects.filter(user=user).values_list(
                "team", flat=True
            )
            return Expense.objects.filter(Q(user=user) | Q(team__in=user_teams))

    def get_queryset(self):
        queryset = self.get_base_queryset().select_related("category", "team")

        selected_categories = self.request.GET.getlist("category")
        if selected_categories:
            queryset = queryset.filter(category__id__in=selected_categories)
        
        min_value = self.request.GET.get("min")
        if min_value:
            queryset = queryset.filter(amount_rub__gte=min_value)

        max_value = self.request.GET.get("max")
        if max_value:
            queryset = queryset.filter(amount_rub__lte=max_value)

        return queryset.order_by("-date", "-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        team_id = self.kwargs.get("team_id")
        
        base_qs = self.get_base_queryset()
        
        agg = base_qs.aggregate(
            min_possible=Min("amount_rub"),
            max_possible=Max("amount_rub"),
        )

        min_p = agg["min_possible"] or 0
        max_p = agg["max_possible"] or 10000

        if min_p == max_p:
            max_p = min_p + 100
        else:
            if max_p % 100 != 0:
                max_p = ceil(max_p / 100) * 100

        context["min_possible"] = min_p
        context["max_possible"] = max_p

        if team_id:
            context["current_team"] = Team.objects.get(id=team_id)
            context["user_teams"] = None
            context["all_categories"] = ExpenseCategory.objects.filter(team_id=team_id)
            context["has_any_expenses"] = Expense.objects.filter(
                team_id=team_id
            ).exists()
            context["selected_categories"] = []
        else:
            context["current_team"] = None
            context["user_teams"] = Team.objects.filter(members__user=user).distinct()

            context["all_categories"] = (
                ExpenseCategory.objects.filter(
                    Q(user=user)
                    | Q(
                        team__in=TeamMember.objects.filter(user=user).values_list(
                            "team", flat=True
                        )
                    )
                )
                .distinct()
                .order_by("name")
            )

            user_teams = TeamMember.objects.filter(user=user).values_list(
                "team", flat=True
            )
            context["has_any_expenses"] = Expense.objects.filter(
                Q(user=user) | Q(team__in=user_teams)
            ).exists()

            context["selected_categories"] = self.request.GET.getlist("category")

        return context


class ExpenseCategoryListView(TeamMemberAccessMixin, ListView):
    model = ExpenseCategory
    template_name = "expenses/expense_category_list.html"
    context_object_name = "categories"

    def get_queryset(self):
        user = self.request.user
        team_id = self.kwargs.get("team_id")

        if team_id:
            queryset = ExpenseCategory.objects.filter(team_id=team_id)
        else:
            user_teams = TeamMember.objects.filter(user=user).values_list(
                "team", flat=True
            )
            queryset = ExpenseCategory.objects.filter(
                Q(user=user) | Q(team__in=user_teams)
            ).distinct()

        return queryset.annotate(
            expense_count=Count("expenses"), total_amount=Sum("expenses__amount_rub")
        ).order_by("name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team_id = self.kwargs.get("team_id")
        context["current_team"] = Team.objects.get(id=team_id) if team_id else None
        return context
