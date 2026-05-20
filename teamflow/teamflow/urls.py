from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("expenses/", include("expenses.urls")),
    path("tasks/", include("tasks.urls")),
    path("teams/", include("teams.urls")),
    path("profiles/", include("profiles.urls")),
    path("accounts/", include("accounts.urls")),
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    import debug_toolbar
    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns

handler400 = "core.errors.handler400"
handler404 = "core.errors.handler404"
handler403 = "core.errors.handler403"
handler500 = "core.errors.handler500"
