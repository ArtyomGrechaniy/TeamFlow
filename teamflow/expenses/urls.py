from django.urls import path

from . import views

app_name = 'expenses'


urlpatterns = [
    path('', views.ExpenseListView.as_view(), name='expense_list'),
    path('add/', views.ExpenseCreateView.as_view(), name='expense_create'),
    path('<int:pk>/', views.ExpenseDetailView.as_view(), name='expense_detail'),
    path('<int:pk>/edit/', views.ExpenseUpdateView.as_view(), name='expense_update'),
    path('<int:pk>/delete/', views.ExpenseDeleteView.as_view(), name='expense_delete'),
    path('categories/', views.ExpenseCategoryListView.as_view(), name='category_list'),
    path('category/add/', views.ExpenseCategoryCreateView.as_view(), name='category_create'),
    path('category/<int:pk>/edit/', views.ExpenseCategoryUpdateView.as_view(), name='category_update'),
    path('category/<int:pk>/delete/', views.ExpenseCategoryDeleteView.as_view(), name='category_delete'),
]
