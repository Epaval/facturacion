from datetime import date

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F, Sum
from django.views.generic import TemplateView

from clientes.models import Cliente
from productos.models import Producto
from ventas.models import Venta


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "core/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        hoy = date.today()
        ventas_hoy = Venta.objects.filter(fecha__date=hoy, estado="completada")
        ctx["ventas_hoy"] = ventas_hoy.count()
        ctx["total_hoy"] = ventas_hoy.aggregate(t=Sum("total"))["t"] or 0
        ctx["stock_bajo"] = Producto.objects.filter(activo=True, stock__lte=F("stock_minimo")).count()
        ctx["total_productos"] = Producto.objects.filter(activo=True).count()
        ctx["total_clientes"] = Cliente.objects.count()
        ctx["ultimas_ventas"] = Venta.objects.select_related("cliente", "usuario")[:8]
        return ctx
