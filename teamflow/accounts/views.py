from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeDoneView,
    PasswordChangeView,
)
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView

from .forms import LoginForm, RegisterForm


# ====================== Аутентификация ======================
class RegisterView(CreateView):
    """Регистрация и автоматическая авторизация нового пользователя."""
    form_class = RegisterForm
    template_name = "registration/register.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response

    def get_success_url(self):
        return reverse("profile:profile", kwargs={"username": self.object.username})


class CustomLoginView(LoginView):
    """Авторизация и редирект пользователя на его профиль."""
    template_name = "registration/login.html"
    redirect_authenticated_user = True
    authentication_form = LoginForm

    def get_success_url(self):
        return reverse_lazy(
            "profile:profile", kwargs={"username": self.request.user.username}
        )


class CustomLogoutView(LoginRequiredMixin, LogoutView):
    """Выход из аккаунта для авторизованного пользователя."""
    template_name = "registration/logout.html"
    next_page = reverse_lazy("accounts:login")
    http_method_names = ["get", "post"]


class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    """Позволяет авторизованному пользователю сменить пароль."""
    template_name = "registration/password_change.html"
    success_url = reverse_lazy("accounts:password_change_done")


class CustomPasswordChangeDoneView(LoginRequiredMixin, PasswordChangeDoneView):
    """Показывает страницу успешной смены пароля."""
    template_name = "registration/password_change_done.html"
