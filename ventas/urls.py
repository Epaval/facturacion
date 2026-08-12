from django.urls import path
from . import views
from . import views_caja

app_name = "ventas"

urlpatterns = [
    path("pos/", views.POSView.as_view(), name="pos"),
    path("pago/", views.PagoView.as_view(), name="pago"),
    path("caja/", views_caja.CajaView.as_view(), name="caja"),
    path("caja/cerrar/", views_caja.CajaCerrarView.as_view(), name="caja_cerrar"),
    path("caja/historial/", views_caja.CajaListView.as_view(), name="caja_list"),
    path("caja/<int:pk>/regularizar/", views_caja.CajaRegularizarView.as_view(), name="caja_regularizar"),
    path("caja/<int:pk>/", views_caja.CajaDetailView.as_view(), name="caja_detail"),
    path("", views.VentaListView.as_view(), name="list"),
    path("<int:pk>/", views.VentaDetailView.as_view(), name="detail"),
]
