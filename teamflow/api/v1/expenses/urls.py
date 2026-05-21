from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ExpenseCategoryViewSet, ExpenseViewSet

router = DefaultRouter()
router.register("expenses", ExpenseViewSet, basename="expenses")
router.register(
    "expense_categories",
    ExpenseCategoryViewSet,
    basename="expense_categories",
)


expense_list = ExpenseViewSet.as_view(
    {
        "get": "list",
        "post": "create",
    }
)

expense_detail = ExpenseViewSet.as_view(
    {
        "get": "retrieve",
        "put": "update",
        "patch": "partial_update",
        "delete": "destroy",
    }
)

expense_category_list = ExpenseCategoryViewSet.as_view(
    {
        "get": "list",
        "post": "create",
    }
)

expense_category_detail = ExpenseCategoryViewSet.as_view(
    {
        "get": "retrieve",
        "put": "update",
        "patch": "partial_update",
        "delete": "destroy",
    }
)


team_urls = [
    path(
        "expenses/",
        expense_list,
        name="team_expenses_list",
    ),
    path(
        "expenses/<int:pk>/",
        expense_detail,
        name="team_expenses_detail",
    ),
    path(
        "expense_categories/",
        expense_category_list,
        name="team_expense_categories_list",
    ),
    path(
        "expense_categories/<int:pk>/",
        expense_category_detail,
        name="team_expense_categories_detail",
    ),
]


urlpatterns = [
    path("", include(router.urls)),
    path("teams/<int:team_pk>/", include(team_urls)),
]
