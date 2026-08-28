from django.views.generic import TemplateView
from .models import ImpresoraFiscal
from .licencia_keys import huella_maquina, validar_clave
from django.shortcuts import get_object_or_404
from django.db.models import ProtectedError
from django.views import View
from django.http import HttpResponse
from core.mixins import AdminRequiredMixin
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
        modo = request.POST.get("modo_control", "correlativo")

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
            cfg.modo_control = modo
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
            resultado = validar_clave(clave)
            if not resultado:
                messages.error(request, "Clave inválida o no corresponde a esta máquina.")
            else:
                dias, _h = resultado
                lic.clave = clave
                lic.activada = True
                from django.utils import timezone
                lic.fecha_activacion = timezone.now()
                lic.dias_licencia = dias
                lic.save()
                messages.success(request, f"Licencia activada: {dias} días desde hoy.")
                return redirect("dashboard")
        elif accion == "prueba":
            lic.activada = True
            from django.utils import timezone
            lic.fecha_activacion = timezone.now()
            lic.dias_licencia = 7
            lic.save()
            messages.success(request, "Período de prueba activado: 7 días.")
            return redirect("dashboard")

    return render(request, "core/licencia.html", {"huella": huella_maquina(),
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


class RespaldoView(AdminRequiredMixin, View):
    """Descarga una copia consistente de la BD SQLite (solo admin)."""

    def get(self, request):
        import sqlite3
        import tempfile
        import os
        from datetime import datetime
        from django.db import connection

        connection.ensure_connection()
        tmp = tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False)
        tmp.close()
        dst = sqlite3.connect(tmp.name)
        connection.connection.backup(dst)
        dst.close()
        with open(tmp.name, "rb") as f:
            data = f.read()
        os.unlink(tmp.name)

        nombre = "respaldo_facturacion_{}.sqlite3".format(
            datetime.now().strftime("%Y%m%d_%H%M%S"))
        resp = HttpResponse(data, content_type="application/octet-stream")
        resp["Content-Disposition"] = 'attachment; filename="{}"'.format(nombre)
        return resp


class ImpresoraView(AdminRequiredMixin, TemplateView):
    """Gestión de impresoras fiscales desde el panel (solo admin)."""
    template_name = "core/impresoras.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["impresoras"] = ImpresoraFiscal.objects.all()
        ctx["title"] = "Impresoras fiscales"
        return ctx

    def post(self, request, *args, **kwargs):
        from .models import ImpresoraFiscal as Imp
        pk = request.POST.get("pk")
        nombre = (request.POST.get("nombre") or "").strip()
        serial = (request.POST.get("serial") or "").strip()
        activa = request.POST.get("activa") in ("on", "1")

        if request.POST.get("accion") == "eliminar":
            imp = get_object_or_404(Imp, pk=pk)
            try:
                imp.delete()
                messages.success(request, f"Impresora {imp.nombre} eliminada")
            except ProtectedError:
                messages.error(request, "No se puede eliminar: tiene cajas asociadas. Desactívala.")
        elif pk:
            imp = get_object_or_404(Imp, pk=pk)
            if nombre:
                imp.nombre = nombre
            if serial:
                imp.serial = serial
            imp.activa = activa
            imp.conexion = request.POST.get("conexion", imp.conexion)
            imp.puerto_serial = (request.POST.get("puerto_serial") or "").strip() or imp.puerto_serial
            imp.ip = (request.POST.get("ip") or "").strip()
            imp.nombre_compartido = (request.POST.get("nombre_compartido") or "").strip()
            try:
                imp.baud = int(request.POST.get("baud") or imp.baud)
                imp.puerto_red = int(request.POST.get("puerto_red") or imp.puerto_red)
            except ValueError:
                pass
            imp.save()
            if request.POST.get("accion") == "probar":
                from core.impresion import enviar_ticket
                texto = ("=== TICKET DE PRUEBA ===\n"
                         f"{imp.nombre}  SERIAL: {imp.serial}\n"
                         f"CONEXION: {imp.conexion} - CONFIGURACION OK\n")
                if imp.conexion == "txt":
                    r = HttpResponse(texto, content_type="text/plain; charset=utf-8")
                    r["Content-Disposition"] = 'filename="ticket_prueba.txt"'
                    return r
                ok, msg = enviar_ticket(texto, imp)
                if ok:
                    messages.success(request, f"🖨 Prueba OK: {msg}")
                else:
                    messages.error(request, msg)
            else:
                messages.success(request, f"Impresora {imp.nombre} actualizada")
        else:
            if not nombre or not serial:
                messages.error(request, "Nombre y serial son obligatorios")
            elif Imp.objects.filter(serial=serial).exists():
                messages.error(request, "Ya existe una impresora con ese serial")
            else:
                Imp.objects.create(nombre=nombre, serial=serial, activa=True)
                messages.success(request, f"Impresora {nombre} registrada")
        return redirect("impresoras")
