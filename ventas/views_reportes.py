import csv
from decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views import View
from django.views.generic import ListView

from core.mixins import AdminRequiredMixin
from clientes.models import Cliente
from .models import LibroVenta, NotaCredito, Venta

MESES = [(1, "Enero"), (2, "Febrero"), (3, "Marzo"), (4, "Abril"), (5, "Mayo"), (6, "Junio"),
         (7, "Julio"), (8, "Agosto"), (9, "Septiembre"), (10, "Octubre"), (11, "Noviembre"), (12, "Diciembre")]
ANIOS = [2024, 2025, 2026]


def q2(x):
    """Redondea a 2 decimales (corrige floats de Sum en SQLite)."""
    if x is None:
        return Decimal("0.00")
    return Decimal(str(x)).quantize(Decimal("0.01"))


class LibroVentasView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    template_name = "ventas/libro_ventas.html"
    context_object_name = "libro_ventas"
    paginate_by = 50

    def get_queryset(self):
        qs = LibroVenta.objects.select_related("venta").all()
        mes = self.request.GET.get("mes")
        anio = self.request.GET.get("anio")
        if mes:
            qs = qs.filter(fecha_factura__month=int(mes))
        if anio:
            qs = qs.filter(fecha_factura__year=int(anio))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        t = self.get_queryset().aggregate(
            tf=Sum("total_facturado"), ex=Sum("exento"), bi=Sum("base_imponible_iva"),
            iv=Sum("monto_iva"), nc=Sum("notas_credito_total"))
        tf, ex, bi, iv, nc = q2(t["tf"]), q2(t["ex"]), q2(t["bi"]), q2(t["iv"]), q2(t["nc"])
        ctx.update({
            "title": "Libro de ventas",
            "mes": self.request.GET.get("mes", ""),
            "anio": self.request.GET.get("anio", ""),
            "meses": MESES, "anios": ANIOS,
            "total_facturado": tf, "total_exento": ex, "total_base": bi,
            "total_iva": iv, "total_nc": nc, "total_neto": tf - nc,
        })
        return ctx


class ReporteFiscalView(LoginRequiredMixin, AdminRequiredMixin, View):
    def get(self, request):
        hoy = timezone.now()
        mes = int(request.GET.get("mes") or hoy.month)
        anio = int(request.GET.get("anio") or hoy.year)

        ventas = Venta.objects.filter(fecha__year=anio, fecha__month=mes, estado="completada").select_related("cliente", "usuario")
        notas = NotaCredito.objects.filter(fecha__year=anio, fecha__month=mes)

        total_ventas = q2(ventas.aggregate(s=Sum("total"))["s"])
        total_base = q2(ventas.aggregate(s=Sum("base_imponible"))["s"])
        total_iva = q2(ventas.aggregate(s=Sum("monto_iva"))["s"])
        total_notas = q2(notas.aggregate(s=Sum("total"))["s"])

        por_metodo = []
        for metodo, label in Venta.METODOS_PAGO:
            t = q2(ventas.filter(metodo_pago=metodo).aggregate(s=Sum("total"))["s"])
            if t > 0:
                por_metodo.append((label, t, ventas.filter(metodo_pago=metodo).count()))

        top_clientes = []
        for cv in ventas.exclude(cliente=None).values("cliente").annotate(t=Sum("total")).order_by("-t")[:10]:
            c = Cliente.objects.filter(pk=cv["cliente"]).first()
            if c:
                top_clientes.append({"cliente": c, "total": q2(cv["t"]), "n": ventas.filter(cliente=c).count()})

        ctx = {
            "title": f"Reporte fiscal {mes}/{anio}",
            "mes": mes, "anio": anio, "meses": MESES, "anios": ANIOS,
            "total_ventas": total_ventas, "total_base": total_base, "total_iva": total_iva,
            "total_notas": total_notas, "total_neto": total_ventas - total_notas,
            "cantidad_ventas": ventas.count(), "cantidad_notas": notas.count(),
            "por_metodo": por_metodo, "top_clientes": top_clientes,
            "ventas": ventas, "notas": notas,
        }
        return render(request, "ventas/reporte_fiscal.html", ctx)


class ReporteFiscalPrintView(LoginRequiredMixin, AdminRequiredMixin, View):
    def get(self, request):
        from core.models import ConfigNegocio
        hoy = timezone.now()
        mes = int(request.GET.get("mes") or hoy.month)
        anio = int(request.GET.get("anio") or hoy.year)

        ventas = Venta.objects.filter(fecha__year=anio, fecha__month=mes, estado="completada").select_related("cliente", "usuario").order_by("numero")
        notas = NotaCredito.objects.filter(fecha__year=anio, fecha__month=mes).order_by("id")

        total_ventas = q2(ventas.aggregate(s=Sum("total"))["s"])
        total_base = q2(ventas.aggregate(s=Sum("base_imponible"))["s"])
        total_iva = q2(ventas.aggregate(s=Sum("monto_iva"))["s"])
        total_notas = q2(notas.aggregate(s=Sum("total"))["s"])

        por_metodo = []
        for metodo, label in Venta.METODOS_PAGO:
            t = q2(ventas.filter(metodo_pago=metodo).aggregate(s=Sum("total"))["s"])
            if t > 0:
                por_metodo.append((label, t, ventas.filter(metodo_pago=metodo).count()))

        ctx = {
            "mes": mes, "anio": anio,
            "config": ConfigNegocio.get(),
            "total_ventas": total_ventas, "total_base": total_base, "total_iva": total_iva,
            "total_notas": total_notas, "total_neto": total_ventas - total_notas,
            "cantidad_ventas": ventas.count(), "cantidad_notas": notas.count(),
            "por_metodo": por_metodo, "ventas": ventas, "notas": notas,
        }
        return render(request, "ventas/reporte_fiscal_print.html", ctx)


class ExportarLibroVentasCSV(LoginRequiredMixin, AdminRequiredMixin, View):
    def get(self, request):
        mes = request.GET.get("mes")
        anio = request.GET.get("anio")
        qs = LibroVenta.objects.all()
        if mes:
            qs = qs.filter(fecha_factura__month=int(mes))
        if anio:
            qs = qs.filter(fecha_factura__year=int(anio))

        response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
        nombre = f"libro_ventas_{anio or 'todos'}_{mes or 'todos'}.csv"
        response["Content-Disposition"] = f'attachment; filename="{nombre}"'
        response.write("\ufeff")
        w = csv.writer(response, delimiter=";")
        w.writerow(["N° Control", "N° Factura", "Fecha", "Cliente", "RIF/CI", "Total Facturado",
                    "Exento", "Base Imponible", "IVA %", "Monto IVA", "Notas Crédito", "Total Neto"])
        for lv in qs:
            f = lambda x: str(q2(x)).replace(".", ",")
            w.writerow([lv.numero_control, lv.numero_factura, lv.fecha_factura.strftime("%d/%m/%Y"),
                        lv.cliente_nombre, lv.cliente_rif, f(lv.total_facturado), f(lv.exento),
                        f(lv.base_imponible_iva), f(lv.alicuota_iva), f(lv.monto_iva),
                        f(lv.notas_credito_total), f(lv.total_neto)])
        return response


class ExportarReporteFiscalCSV(LoginRequiredMixin, AdminRequiredMixin, View):
    def get(self, request):
        hoy = timezone.now()
        mes = int(request.GET.get("mes") or hoy.month)
        anio = int(request.GET.get("anio") or hoy.year)

        ventas = Venta.objects.filter(fecha__year=anio, fecha__month=mes, estado="completada").select_related("cliente", "usuario").order_by("numero")
        notas = NotaCredito.objects.filter(fecha__year=anio, fecha__month=mes).order_by("id")

        response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
        response["Content-Disposition"] = f'attachment; filename="reporte_fiscal_{anio}-{mes:02d}.csv"'
        response.write("\ufeff")
        w = csv.writer(response, delimiter=";")
        f = lambda x: str(q2(x)).replace(".", ",")

        w.writerow([f"REPORTE FISCAL SENIAT {mes:02d}/{anio}"])
        w.writerow([])
        w.writerow(["VENTAS DEL PERIODO"])
        w.writerow(["N° Factura", "N° Control", "Fecha", "Cliente", "RIF/CI", "Método", "Base imponible", "IVA", "Total"])
        tv = tb = ti = Decimal("0")
        for v in ventas:
            lv = LibroVenta.objects.filter(venta=v).first()
            w.writerow([f"{v.numero:06d}", lv.numero_control if lv else "", v.fecha.strftime("%d/%m/%Y"),
                        v.cliente.full_name if v.cliente else "Consumidor final",
                        v.cliente.ci_nit if v.cliente else "", v.get_metodo_pago_display(),
                        f(v.base_imponible), f(v.monto_iva), f(v.total)])
            tv += q2(v.total); tb += q2(v.base_imponible); ti += q2(v.monto_iva)
        w.writerow([])
        w.writerow(["TOTALES", "", "", "", "", "", f(tb), f(ti), f(tv)])
        w.writerow([])
        w.writerow(["NOTAS DE CREDITO DEL PERIODO"])
        w.writerow(["N° NC", "Factura asociada", "Fecha", "Cliente", "Motivo", "Total"])
        tn = Decimal("0")
        for n in notas:
            w.writerow([n.id, f"{n.factura.numero:06d}", n.fecha.strftime("%d/%m/%Y"),
                        n.factura.cliente.full_name if n.factura.cliente else "Consumidor final",
                        n.motivo, f(n.total)])
            tn += q2(n.total)
        w.writerow([])
        w.writerow(["TOTAL NOTAS DE CREDITO", "", "", "", "", f(tn)])
        w.writerow(["TOTAL NETO (VENTAS - NC)", "", "", "", "", f(tv - tn)])
        return response
