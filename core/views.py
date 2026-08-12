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
        if not self.request.user.es_admin:
            ventas_hoy = ventas_hoy.filter(usuario=self.request.user)
        ctx["ventas_hoy"] = ventas_hoy.count()
        ctx["total_hoy"] = ventas_hoy.aggregate(t=Sum("total"))["t"] or 0
        ctx["stock_bajo"] = Producto.objects.filter(activo=True, stock__lte=F("stock_minimo")).count()
        ctx["total_productos"] = Producto.objects.filter(activo=True).count()
        ctx["total_clientes"] = Cliente.objects.count()
        ultimas = Venta.objects.select_related("cliente", "usuario")
        if not self.request.user.es_admin:
            ultimas = ultimas.filter(usuario=self.request.user)
        ctx["ultimas_ventas"] = ultimas[:8]
        return ctx
