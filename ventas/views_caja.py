from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View
from django.views.generic import ListView

from .models import Caja, Pago, Venta


def resumen_caja(caja):
    """Esperado en gaveta = inicial + efectivo recibido - vuelto entregado."""
    ventas = Venta.objects.filter(
        usuario=caja.usuario, estado="completada", fecha__gte=caja.fecha_apertura
    )
    if caja.fecha_cierre:
        ventas = ventas.filter(fecha__lte=caja.fecha_cierre)

    total_vendido = ventas.aggregate(s=Sum("total"))["s"] or Decimal("0.00")
    por_metodo = list(
        Pago.objects.filter(venta__in=ventas)
        .values("metodo").annotate(s=Sum("monto")).order_by("metodo")
    )
    efectivo = sum((p["s"] for p in por_metodo if p["metodo"] == "efectivo"), Decimal("0.00"))
    cambio = ventas.aggregate(s=Sum("cambio"))["s"] or Decimal("0.00")

    return {
        "total_vendido": total_vendido,
        "n_ventas": ventas.count(),
        "por_metodo": por_metodo,
        "efectivo": efectivo,
        "cambio": cambio,
        "esperado": caja.monto_inicial + efectivo - cambio,
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
