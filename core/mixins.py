from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages


class AdminRequiredMixin(UserPassesTestMixin):
    """Solo administradores (rol admin o superuser)."""

    def test_func(self):
        # Verificar si el usuario está autenticado
        if not self.request.user.is_authenticated:
            return False
        
        # Verificar si tiene el atributo es_admin
        return getattr(self.request.user, 'es_admin', False)

    def handle_no_permission(self):
        """Redirigir al login si no está autenticado o no es admin."""
        if not self.request.user.is_authenticated:
            messages.warning(self.request, "Debes iniciar sesión para acceder a esta sección")
            return redirect('accounts:login')
        
        # Si está autenticado pero no es admin
        messages.error(self.request, "No tienes permisos de administrador para acceder a esta sección")
        raise PermissionDenied("No tienes permisos de administrador")