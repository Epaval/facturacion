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
]
