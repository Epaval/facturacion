import re

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from accounts.models import Empleado
from core.models import ConfigNegocio, Licencia
from .forms import ConfigNegocioForm, LicenciaForm


def setup_view(request):
    """Primera vez: crea admin + datos del negocio."""
    if Empleado.objects.filter(is_superuser=True).exists():
        return redirect("dashboard")

    if request.method == "POST":
        form_user = request.POST
        username = form_user.get("username", "").strip()
        password1 = form_user.get("password1", "")
        password2 = form_user.get("password2", "")
        form_cfg = ConfigNegocioForm(request.POST, request.FILES)

        errores = []
        if not username:
            errores.append("Usuario requerido")
        if len(password1) < 6:
            errores.append("Contraseña mínima 6 caracteres")
        if password1 != password2:
            errores.append("Las contraseñas no coinciden")
        if not form_cfg.is_valid():
            errores.append("Revisa los datos del negocio")

        if errores:
            for e in errores:
                messages.error(request, e)
        else:
            admin = Empleado.objects.create_superuser(
                username=username, password=password1,
                nombres=form_user.get("nombres", "Admin") or "Admin",
                apellidos=form_user.get("apellidos", "") or "Sistema",
                rol="admin",
            )
            cfg = form_cfg.save(commit=False)
            cfg.pk = 1
            cfg.save()
            login(request, admin, backend="django.contrib.auth.backends.ModelBackend")
            messages.success(request, "Sistema inicializado. Bienvenido.")
            return redirect("licencia")

    return render(request, "core/setup.html", {
        "form_cfg": ConfigNegocioForm(),
        "title": "Primer arranque",
    })


@login_required
def licencia_view(request):
    """Activar / ver estado de la licencia. Sin perpetua."""
    lic = Licencia.get()

    if request.method == "POST":
        accion = request.POST.get("accion")
        if accion == "activar":
            clave = request.POST.get("clave", "").strip().upper()
            if not re.fullmatch(r"[A-Z0-9\-]{10,30}", clave):
                messages.error(request, "Clave inválida. Debe ser alfanumérica.")
            else:
                lic.clave = clave
                lic.activada = True
                from django.utils import timezone
                lic.fecha_activacion = timezone.now()
                lic.save()
                messages.success(request, f"Licencia activada: 365 días desde hoy.")
                return redirect("dashboard")
        elif accion == "prueba":
            lic.activada = True
            from django.utils import timezone
            lic.fecha_activacion = timezone.now()
            lic.dias_licencia = 7
            lic.save()
            messages.success(request, "Período de prueba activado: 7 días.")
            return redirect("dashboard")

    return render(request, "core/licencia.html", {
        "lic": lic,
        "title": "Licencia del sistema",
    })


def config_negocio_view(request):
    """Admin modifica los datos del negocio."""
    if not request.user.es_admin:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    cfg = ConfigNegocio.get()
    if request.method == "POST":
        form = ConfigNegocioForm(request.POST, request.FILES, instance=cfg)
        if form.is_valid():
            form.save()
            messages.success(request, "Datos del negocio actualizados.")
            return redirect("config_negocio")
    else:
        form = ConfigNegocioForm(instance=cfg)
    return render(request, "core/config_negocio.html", {
        "form": form, "title": "Datos del negocio",
    })
