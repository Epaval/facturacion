import re
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View
from django.views.generic import ListView

from clientes.models import Cliente
from .models import Caja, Pago, Venta


def resumen_caja(caja):
    """Esperado en gaveta = inicial + efectivo recibido - vuelto entregado."""
    ventas = Venta.objects.filter(
        usuario=caja.usuario, estado="completada", fecha__gte=caja.fecha_apertura
    )
    if caja.fecha_cierre:
        ventas = ventas.filter(fecha__lte=caja.fecha_cierre)

    dos = Decimal("0.01")
    total_vendido = (ventas.aggregate(s=Sum("total"))["s"] or Decimal("0.00")).quantize(dos)
    por_metodo = list(
        Pago.objects.filter(venta__in=ventas)
        .values("metodo").annotate(s=Sum("monto")).order_by("metodo")
    )
    efectivo = sum((p["s"] for p in por_metodo if p["metodo"] == "efectivo"), Decimal("0.00")).quantize(dos)
    cambio = (ventas.aggregate(s=Sum("cambio"))["s"] or Decimal("0.00")).quantize(dos)

    return {
        "total_vendido": total_vendido,
        "n_ventas": ventas.count(),
        "por_metodo": por_metodo,
        "efectivo": efectivo,
        "cambio": cambio,
        "esperado": (caja.monto_inicial + efectivo - cambio).quantize(dos),
    }


class CajaView(LoginRequiredMixin, View):
    """Sin caja abierta: formulario de apertura. Con caja: estado en vivo."""

    def get(self, request):
        caja = Caja.objects.filter(usuario=request.user, estado="abierta").first()
        ctx = {"caja": caja, "title": "Caja"}
        if caja:
            ctx.update(resumen_caja(caja))
        return render(request, "ventas/caja.html", ctx)

    def post(self, request):
        if Caja.objects.filter(usuario=request.user, estado="abierta").exists():
            messages.info(request, "Ya tienes una caja abierta")
            return redirect("ventas:caja")
        try:
            inicial = Decimal(request.POST.get("monto_inicial", "0").replace(",", ".") or "0")
        except InvalidOperation:
            inicial = Decimal("0")
        Caja.objects.create(usuario=request.user, monto_inicial=inicial)
        messages.success(request, "Caja abierta. ¡Buenas ventas!")
        return redirect("ventas:pos")


class CajaCerrarView(LoginRequiredMixin, View):
    def get(self, request):
        caja = get_object_or_404(Caja, usuario=request.user, estado="abierta")
        ctx = {"caja": caja, "title": "Cierre de caja"}
        ctx.update(resumen_caja(caja))
        return render(request, "ventas/caja_cerrar.html", ctx)

    def post(self, request):
        caja = get_object_or_404(Caja, usuario=request.user, estado="abierta")
        try:
            contado = Decimal(request.POST.get("monto_contado", "0").replace(",", ".") or "0")
        except InvalidOperation:
            contado = Decimal("0")

        r = resumen_caja(caja)
        caja.monto_contado = contado
        caja.esperado = r["esperado"]
        caja.diferencia = contado - r["esperado"]
        caja.fecha_cierre = timezone.now()
        caja.estado = "cerrada"
        caja.save()

        if caja.diferencia == 0:
            messages.success(request, "Caja cerrada sin diferencias")
        elif caja.diferencia > 0:
            messages.warning(request, f"Caja cerrada con SOBRANTE de Bs {caja.diferencia}")
        else:
            messages.error(request, f"Caja cerrada con FALTANTE de Bs {abs(caja.diferencia)}")
        return redirect("ventas:caja_list")


class CajaListView(LoginRequiredMixin, ListView):
    template_name = "ventas/caja_list.html"
    context_object_name = "object_list"
    paginate_by = 15

    def get_queryset(self):
        qs = Caja.objects.select_related("usuario")
        if not self.request.user.es_admin:
            qs = qs.filter(usuario=self.request.user)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Historial de cajas"
        return ctx


class CajaRegularizarView(LoginRequiredMixin, View):
    """Solo admin: destina la diferencia de una caja cerrada."""

    def get(self, request, pk):
        if not request.user.es_admin:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        caja = get_object_or_404(Caja, pk=pk, estado="cerrada")
        q_cliente = request.GET.get("q_cliente", "").strip()
        sel_id = request.GET.get("sel")
        seleccionado = Cliente.objects.filter(pk=sel_id).first() if sel_id else None
        resultados = None
        if q_cliente and re.fullmatch(r"(V|J|G)?\d{6,9}", q_cliente.upper()):
            exacto = Cliente.objects.filter(ci_nit__iexact=q_cliente).first()
            if exacto:
                return redirect(f"{request.path}?sel={exacto.pk}")
        if q_cliente:
            resultados = Cliente.objects.filter(
                Q(ci_nit__icontains=q_cliente)
                | Q(nombres__icontains=q_cliente)
                | Q(apellidos__icontains=q_cliente)
            )[:8]
        return render(request, "ventas/caja_regularizar.html", {
            "caja": caja,
            "q_cliente": q_cliente,
            "resultados": resultados,
            "seleccionado": seleccionado,
            "title": "Regularizar caja",
        })

    def post(self, request, pk):
        if not request.user.es_admin:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        caja = get_object_or_404(Caja, pk=pk, estado="cerrada")
        if not caja.diferencia:
            messages.info(request, "Esta caja no tiene diferencia que regularizar")
            return redirect("ventas:caja_list")

        destino = request.POST.get("destino")
        validos = ["cajero"] if caja.diferencia < 0 else ["cliente", "ingreso"]
        if destino not in validos:
            messages.error(request, "Destino no válido para esta diferencia")
            return redirect("ventas:caja_regularizar", pk=caja.pk)

        previo = ""
        if caja.regularizada:
            previo = caja.get_destino_diferencia_display()
            if caja.cliente_reclamo:
                previo += f" / {caja.cliente_reclamo.full_name}"

        if destino == "cliente":
            cliente_id = request.POST.get("cliente_reclamo")
            if not cliente_id:
                messages.error(request, "Indica a qué cliente se devolvió el sobrante")
                return redirect("ventas:caja_regularizar", pk=caja.pk)
            caja.cliente_reclamo_id = cliente_id
        else:
            caja.cliente_reclamo = None
        caja.destino_diferencia = destino
        caja.regularizada = True
        caja.regularizada_por = request.user
        caja.fecha_regularizacion = timezone.now()
        caja.nota_regularizacion = request.POST.get("nota", "").strip()

        linea = f"{timezone.now():%d/%m/%Y %H:%M} · {request.user.full_name} · destino: {caja.get_destino_diferencia_display()}"
        if caja.cliente_reclamo:
            linea += f" · cliente: {caja.cliente_reclamo.full_name}"
        if previo:
            linea += f" · antes: {previo}"
        if caja.nota_regularizacion:
            linea += f" · nota: {caja.nota_regularizacion}"
        caja.historial_regularizacion = (caja.historial_regularizacion + "\n" + linea).strip()
        caja.save()
        messages.success(request, f"Caja #{caja.id} regularizada: {caja.get_destino_diferencia_display()}")
        return redirect("ventas:caja_list")


class CajaDetailView(LoginRequiredMixin, View):
    """Trazabilidad completa: caja, cajero, día, diferencia y clientes con vuelto."""

    def get(self, request, pk):
        caja = get_object_or_404(Caja, pk=pk)
        if not request.user.es_admin and caja.usuario_id != request.user.id:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        ctx = {"caja": caja, "title": f"Caja #{caja.id}"}
        ctx.update(resumen_caja(caja))
        fin = caja.fecha_cierre or timezone.now()
        ctx["ventas_caja"] = Venta.objects.filter(
            usuario=caja.usuario, estado="completada",
            fecha__gte=caja.fecha_apertura, fecha__lte=fin,
        ).select_related("cliente").prefetch_related("pagos").order_by("-fecha")
        return render(request, "ventas/caja_detail.html", ctx)
