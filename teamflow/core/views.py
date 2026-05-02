from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, TemplateView

from .forms import LoginForm, RegisterForm
    

class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = 'registration/register.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response

    def get_success_url(self):
        return reverse('profile:profile', kwargs={'username': self.object.username})


class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    redirect_authenticated_user = True
    authentication_form = LoginForm

    def get_success_url(self):
        return reverse_lazy('profile:profile', kwargs={'username': self.request.user.username})


class HomeView(TemplateView):
    template_name = 'core/index.html'
