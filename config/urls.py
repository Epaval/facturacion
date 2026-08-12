from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from core import views as core_views
from core.views import DashboardView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", DashboardView.as_view(), name="dashboard"),
    path("setup/", core_views.setup_view, name="setup"),
    path("licencia/", core_views.licencia_view, name="licencia"),
    path("config-negocio/", core_views.config_negocio_view, name="config_negocio"),
    path("accounts/", include("accounts.urls")),
    path("productos/", include("productos.urls")),
    path("clientes/", include("clientes.urls")),
    path("ventas/", include("ventas.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
