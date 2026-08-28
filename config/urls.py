from django.views.generic import TemplateView as _TV
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
    path("respaldo/", core_views.RespaldoView.as_view(), name="respaldo"),
    path("impresoras/", core_views.ImpresoraView.as_view(), name="impresoras"),
    path("accounts/", include("accounts.urls")),
    path("productos/", include("productos.urls")),
    path("clientes/", include("clientes.urls")),
    path("ventas/", include("ventas.urls")),
    path("impresoras/ayuda/", _TV.as_view(template_name="core/impresoras_ayuda.html"), name="impresoras_ayuda"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
