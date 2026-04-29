from django.urls import path, include
from . import views

app_name = 'teams'

urlpatterns = [
    path('', views.TeamListView.as_view(), name='team_list'),
    path('create/', views.TeamCreateView.as_view(), name='team_create'),
    path('<int:pk>/', views.TeamDetailView.as_view(), name='team_detail'),
    path('<int:pk>/edit/', views.TeamUpdateView.as_view(), name='team_update'),
    path('<int:pk>/delete/', views.TeamDeleteView.as_view(), name='team_delete'),
    path('<int:team_id>/expenses/', include(('expenses.urls'))),
    path('<int:team_id>/tasks/', include(('tasks.urls'))),
    path('join/', views.TeamJoinView.as_view(), name='team_join'),
    path('<int:pk>/leave/', views.TeamLeaveView.as_view(), name='team_leave'),
    path('<int:pk>/members/', views.TeamMemberListView.as_view(), name='team_member_list'),
    path('<int:pk>/members/<int:user_id>/kick/', views.TeamMemberKickView.as_view(), name='team_member_kick'),
    path('<int:pk>/members/<int:user_id>/role/', views.TeamMemberRoleChangeView.as_view(), name='team_member_role'),
]