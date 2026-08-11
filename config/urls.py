from django.contrib import admin
from django.urls import include, path

from core.views import DashboardView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("cuenta/", include("accounts.urls")),
    path("", DashboardView.as_view(), name="dashboard"),
    path("clientes/", include("clientes.urls")),
    path("productos/", include("productos.urls")),
    path("ventas/", include("ventas.urls")),
]
