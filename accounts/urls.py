from . import views
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

app_name = "accounts"

urlpatterns = [
    path("usuarios/", views.UsuarioListView.as_view(), name="usuarios"),
    path("usuarios/nuevo/", views.UsuarioCreateView.as_view(), name="usuario_new"),
    path("usuarios/<int:pk>/", views.UsuarioUpdateView.as_view(), name="usuario_edit"),
    path("login/", LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
]
