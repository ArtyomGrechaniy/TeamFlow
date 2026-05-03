from django.urls import path

from . import views

app_name = 'profile'

urlpatterns = [
    path('statistic', views.ProfileStatisticsView.as_view(), name='profile_statistic'),
    path('<str:username>/statistic/', views.ProfileStatisticsView.as_view(), name='profile_public_statistic'),
    path('edit/', views.ProfileUpdateView.as_view(), name='profile_edit'),
    path('<str:username>/', views.ProfileView.as_view(), name='profile'),
]
