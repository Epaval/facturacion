from django.urls import path
from . import views

app_name = "productos"

urlpatterns = [
    path("importar/", views.ProductoImportView.as_view(), name="importar"),
    path("", views.ProductoListView.as_view(), name="list"),
    path("buscar/", views.ProductoListView.as_view(), name="buscar"),
    path("nuevo/", views.ProductoCreateView.as_view(), name="create"),
    path("<int:pk>/editar/", views.ProductoUpdateView.as_view(), name="update"),
    path("buscar-global/", views.buscar_global, name="buscar_global"),
    path("kardex/", views.kardex, name="kardex"),
    path("ajuste/", views.ajuste_stock, name="ajuste_stock"),
    path("conteo/", views.conteo_fisico, name="conteo"),
    path("stock-negativo/", views.stock_negativo, name="stock_negativo"),
]
