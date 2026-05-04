from django.views.generic import TemplateView


class HomeView(TemplateView):
    """Отоборажает главную страницу проекта."""
    template_name = "core/index.html"
