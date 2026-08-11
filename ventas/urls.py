from django.urls import path
from . import views

app_name = "ventas"

urlpatterns = [
    path("pos/", views.POSView.as_view(), name="pos"),
    path("pago/", views.PagoView.as_view(), name="pago"),
    path("", views.VentaListView.as_view(), name="list"),
    path("<int:pk>/", views.VentaDetailView.as_view(), name="detail"),
]
