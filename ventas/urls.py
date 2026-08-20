from django.urls import path
from . import views
from . import views_caja
from . import views_notas_credito

app_name = "ventas"

urlpatterns = [
    path("pos/", views.POSView.as_view(), name="pos"),
    path("pago/", views.PagoView.as_view(), name="pago"),
    path("caja/", views_caja.CajaView.as_view(), name="caja"),
    path("caja/cerrar/", views_caja.CajaCerrarView.as_view(), name="caja_cerrar"),
    path("caja/historial/", views_caja.CajaListView.as_view(), name="caja_list"),
    path("caja/<int:pk>/regularizar/", views_caja.CajaRegularizarView.as_view(), name="caja_regularizar"),
    path("caja/<int:pk>/", views_caja.CajaDetailView.as_view(), name="caja_detail"),
    path("notas-credito/", views_notas_credito.NotaCreditoListView.as_view(), name="notas_credito_list"),
    path("notas-credito/nueva/", views_notas_credito.NotaCreditoCreateView.as_view(), name="notas_credito_create"),
    path("notas-credito/autorizar/", views_notas_credito.NotaCreditoConfirmarView.as_view(), name="notas_credito_autorizar"),
    path("notas-credito/<int:pk>/", views_notas_credito.NotaCreditoDetailView.as_view(), name="notas_credito_detail"),
    path("", views.VentaListView.as_view(), name="list"),
    path("<int:pk>/marcar-impresa/", views.MarcarImpresaView.as_view(), name="marcar_impresa"),
    path("<int:pk>/", views.VentaDetailView.as_view(), name="detail"),
]
