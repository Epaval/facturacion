from django.urls import path
from . import views

app_name = "clientes"

urlpatterns = [
    path("", views.ClienteListView.as_view(), name="list"),
    path("buscar/", views.ClienteListView.as_view(), name="buscar"),
    path("nuevo/", views.ClienteCreateView.as_view(), name="create"),
    path("<int:pk>/editar/", views.ClienteUpdateView.as_view(), name="update"),
]
