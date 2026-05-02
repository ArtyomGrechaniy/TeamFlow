from django.contrib.auth.views import LogoutView
from django.urls import path, include, reverse_lazy

from . import views

app_name = 'core'


accounts_urls = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page=reverse_lazy('core:login'), template_name=('registration/logout.html'), http_method_names=['get', 'post']), name='logout'),
]


urlpatterns = [
    path('accounts/', include(accounts_urls)),
    path('', views.HomeView.as_view(), name='home'),
]
