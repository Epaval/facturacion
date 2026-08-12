from django.shortcuts import redirect
from django.urls import reverse

from accounts.models import Empleado


EXCEPT_PATHS = ("/setup/", "/static/", "/media/", "/favicon.ico", "/accounts/login/", "/accounts/logout/")


class SetupMiddleware:
    """Si no hay admin creado, obliga a ir a /setup/."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not any(request.path.startswith(p) for p in EXCEPT_PATHS):
            if not Empleado.objects.filter(is_superuser=True).exists():
                return redirect(reverse("setup"))
        return self.get_response(request)


class LicenseMiddleware:
    """Si la licencia está vencida, bloquea todo menos /licencia/ y estáticos."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if any(request.path.startswith(p) for p in EXCEPT_PATHS):
            return self.get_response(request)

        # Evita importar en ciclo
        from core.models import Licencia
        lic = Licencia.get()
        if (lic.esta_vencida or not lic.activada) and not request.path.startswith(reverse("licencia")):
            return redirect(reverse("licencia"))
        return self.get_response(request)
