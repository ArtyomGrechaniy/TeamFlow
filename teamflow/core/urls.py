from django.urls import include, path

from . import views

app_name = "core"


urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path('api/', include('api.urls')),
]
