from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import DetailView, ListView

from clientes.models import Cliente
from productos.models import Producto

from .models import Pago, Venta


class POSView(LoginRequiredMixin, View):
    """Punto de venta: escáner o búsqueda agrega al ticket en sesión."""

    @staticmethod
    def _agregar(lineas, producto, cantidad):
        en_ticket = sum(Decimal(l["cantidad"]) for l in lineas if l["producto_id"] == producto.id)
        if producto.stock < en_ticket + cantidad:
            return f"Stock insuficiente de {producto.nombre}"
        for l in lineas:
            if l["producto_id"] == producto.id:
                l["cantidad"] = str(Decimal(l["cantidad"]) + cantidad)
                l["subtotal"] = str(Decimal(l["subtotal"]) + cantidad * producto.precio_venta)
                break
        else:
            lineas.append({
                "producto_id": producto.id,
                "nombre": producto.nombre,
                "cantidad": str(cantidad),
                "precio": str(producto.precio_venta),
                "subtotal": str(cantidad * producto.precio_venta),
            })
        return None

    def get(self, request):
        lineas = request.session.get("pos_lineas", [])
        q = request.GET.get("q", "").strip()
        productos = None

        # Clic en fila de resultados: agrega 1 o abre modal si es pesable
        agregar_id = request.GET.get("agregar")
        if agregar_id:
            producto = Producto.objects.filter(activo=True, pk=agregar_id).first()
            if producto:
                if producto.es_pesable:
                    total = sum(Decimal(l["subtotal"]) for l in lineas)
                    return render(request, "ventas/pos.html", {
                        "lineas": lineas, "productos": None, "q": "",
                        "total": total, "modal_producto": producto,
                        "title": "Nueva venta (POS)",
                    })
                error = self._agregar(lineas, producto, Decimal("1"))
                if error:
                    messages.error(request, error)
                else:
                    request.session["pos_lineas"] = lineas
                    messages.success(request, f"{producto.nombre} agregado al ticket")
            return redirect("ventas:pos")

        if q:
            exacto = Producto.objects.filter(activo=True).filter(
                Q(codigo_barras__iexact=q) | Q(nombre__iexact=q)
            ).first()
            if not exacto and len(q) >= 3:
                unicos = Producto.objects.filter(activo=True, codigo_barras__icontains=q)
                if unicos.count() == 1:
                    exacto = unicos.first()
            if exacto and exacto.es_pesable:
                total = sum(Decimal(l["subtotal"]) for l in lineas)
                return render(request, "ventas/pos.html", {
                    "lineas": lineas,
                    "productos": None,
                    "q": "",
                    "total": total,
                    "modal_producto": exacto,
                    "title": "Nueva venta (POS)",
                })
            if exacto:
                error = self._agregar(lineas, exacto, Decimal("1"))
                if error:
                    messages.error(request, error)
                else:
                    request.session["pos_lineas"] = lineas
                    messages.success(request, f"{exacto.nombre} agregado al ticket")
                return redirect("ventas:pos")
            productos = Producto.objects.filter(activo=True).filter(
                Q(nombre__icontains=q) | Q(codigo_barras__icontains=q)
            )[:12]

        total = sum(Decimal(l["subtotal"]) for l in lineas)
        return render(request, "ventas/pos.html", {
            "lineas": lineas,
            "productos": productos,
            "q": q,
            "total": total,
            "title": "Nueva venta (POS)",
        })

    def post(self, request):
        accion = request.POST.get("accion")
        lineas = request.session.get("pos_lineas", [])

        if accion == "agregar":
            producto = get_object_or_404(Producto, pk=request.POST.get("producto"))
            try:
                cantidad = Decimal(request.POST.get("cantidad", "1").replace(",", ".") or "1")
            except InvalidOperation:
                cantidad = Decimal("1")
            error = self._agregar(lineas, producto, cantidad)
            if error:
                messages.error(request, error)
            else:
                request.session["pos_lineas"] = lineas

        elif accion == "quitar":
            try:
                idx = int(request.POST.get("indice"))
                if 0 <= idx < len(lineas):
                    lineas.pop(idx)
            except ValueError:
                pass
            request.session["pos_lineas"] = lineas

        elif accion == "vaciar":
            request.session["pos_lineas"] = []

        elif accion == "pagar":
            if not lineas:
                messages.info(request, "El ticket está vacío")
                return redirect("ventas:pos")
            return redirect("ventas:pago")

        return redirect("ventas:pos")


class PagoView(LoginRequiredMixin, View):
    """Cobro: pagos parciales, vuelto, resto a crédito. La venta se crea al confirmar."""

    def _totales(self, request):
        lineas = request.session.get("pos_lineas", [])
        pagos = request.session.get("pos_pagos", [])
        total = sum(Decimal(l["subtotal"]) for l in lineas)
        pagado = sum(Decimal(p["monto"]) for p in pagos)
        return lineas, pagos, total, pagado

    def get(self, request):
        lineas, pagos, total, pagado = self._totales(request)
        if not lineas:
            return redirect("ventas:pos")
        cliente_id = request.session.get("pos_cliente")
        cliente = Cliente.objects.filter(pk=cliente_id).first() if cliente_id else None
        etiquetas = dict(Pago.METODOS)
        pagos_vista = [dict(p, metodo_label=etiquetas.get(p["metodo"], p["metodo"])) for p in pagos]
        return render(request, "ventas/pago.html", {
            "lineas": lineas, "pagos": pagos_vista,
            "total": total, "pagado": pagado,
            "falta": max(total - pagado, Decimal("0")),
            "cambio": max(pagado - total, Decimal("0")),
            "cliente": cliente,
            "clientes": Cliente.objects.all(),
            "completo": pagado >= total,
            "title": "Cobro de venta",
        })

    def post(self, request):
        accion = request.POST.get("accion")
        lineas, pagos, total, pagado = self._totales(request)
        if not lineas:
            return redirect("ventas:pos")

        if accion == "cliente":
            request.session["pos_cliente"] = request.POST.get("cliente") or None
            return redirect("ventas:pago")

        if accion == "agregar_pago":
            metodo = request.POST.get("metodo", "efectivo")
            try:
                monto = Decimal(request.POST.get("monto", "0").replace(",", ".") or "0")
            except InvalidOperation:
                monto = Decimal("0")
            if monto <= 0:
                messages.error(request, "El monto debe ser mayor a cero")
            else:
                pagos.append({"metodo": metodo, "monto": str(monto)})
                request.session["pos_pagos"] = pagos
            return redirect("ventas:pago")

        if accion == "quitar_pago":
            try:
                idx = int(request.POST.get("indice"))
                if 0 <= idx < len(pagos):
                    pagos.pop(idx)
            except ValueError:
                pass
            request.session["pos_pagos"] = pagos
            return redirect("ventas:pago")

        if accion == "volver":
            return redirect("ventas:pos")

        if accion == "confirmar":
            cliente_id = request.session.get("pos_cliente")
            if not cliente_id:
                messages.error(request, "Selecciona un cliente para confirmar la venta")
                return redirect("ventas:pago")
            if pagado < total:
                messages.error(request, f"Falta completar el pago: Bs {total - pagado}")
                return redirect("ventas:pago")

            with transaction.atomic():
                cliente = Cliente.objects.select_for_update().get(pk=cliente_id)
                metodos = {p["metodo"] for p in pagos}
                metodo_final = metodos.pop() if len(metodos) == 1 else "mixto"

                venta = Venta.objects.create(
                    cliente=cliente, usuario=request.user,
                    subtotal=total, descuento=0, total=total,
                    monto_recibido=pagado,
                    cambio=max(pagado - total, Decimal("0")),
                    metodo_pago=metodo_final,
                )
                for l in lineas:
                    producto = Producto.objects.select_for_update().get(pk=l["producto_id"])
                    venta.detalles.create(
                        producto=producto,
                        cantidad=Decimal(l["cantidad"]),
                        precio_unitario=Decimal(l["precio"]),
                    )
                    producto.stock -= Decimal(l["cantidad"])
                    producto.save()
                for p in pagos:
                    venta.pagos.create(metodo=p["metodo"], monto=Decimal(p["monto"]))

            request.session["pos_lineas"] = []
            request.session["pos_pagos"] = []
            request.session["pos_cliente"] = None
            messages.success(request, f"Venta #{venta.numero} registrada por Bs {venta.total}")
            return redirect("ventas:detail", pk=venta.pk)

        return redirect("ventas:pago")


class VentaListView(LoginRequiredMixin, ListView):
    model = Venta
    template_name = "ventas/venta_list.html"
    context_object_name = "object_list"
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().select_related("cliente", "usuario")
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(Q(numero__icontains=q) | Q(cliente__nombres__icontains=q))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        ctx["title"] = "Historial de ventas"
        return ctx


class VentaDetailView(LoginRequiredMixin, DetailView):
    model = Venta
    template_name = "ventas/venta_detail.html"
    context_object_name = "venta"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = f"Venta #{self.object.numero}"
        return ctx
