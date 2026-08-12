import re
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

from .models import Caja, Pago, Venta


def desglose_iva(total, gravado=None):
    """Precios con IVA 16% incluido. gravado = parte del total que paga IVA."""
    dos = Decimal("0.01")
    if gravado is None:
        gravado = total
    base_grav = (gravado / Decimal("1.16")).quantize(dos)
    iva = (gravado - base_grav).quantize(dos)
    base = (total - gravado) + base_grav
    return base.quantize(dos), iva


def monto_gravado(lineas):
    """Suma los subtotales de líneas cuyo producto paga IVA (dato en vivo)."""
    ids = [l["producto_id"] for l in lineas]
    gravados = set(
        Producto.objects.filter(pk__in=ids, grava_iva=True).values_list("pk", flat=True)
    )
    return sum((Decimal(l["subtotal"]) for l in lineas if l["producto_id"] in gravados), Decimal("0.00"))


def total_items(lineas):
    """Ítems físicos: unidades suman su cantidad; pesables (kg/g/lb) cuentan 1."""
    ids = [l["producto_id"] for l in lineas]
    pesables = set(
        Producto.objects.filter(pk__in=ids, unidad__in=["kg", "g", "lb"]).values_list("pk", flat=True)
    )
    items = 0
    for l in lineas:
        if l["producto_id"] in pesables:
            items += 1
        else:
            items += int(Decimal(l["cantidad"]))
    return items


def ctx_iva(lineas, total):
    gravado = monto_gravado(lineas)
    base, iva = desglose_iva(total, gravado)
    return {"base_imponible": base, "iva_incluido": iva, "total_items": total_items(lineas)}


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
                l["subtotal"] = str((Decimal(l["subtotal"]) + cantidad * producto.precio_venta).quantize(Decimal("0.01")))
                break
        else:
            lineas.append({
                "producto_id": producto.id,
                "nombre": producto.nombre,
                "cantidad": str(cantidad),
                "precio": str(producto.precio_venta),
                "subtotal": str((cantidad * producto.precio_venta).quantize(Decimal("0.01"))),
            })
        return None

    def get(self, request):
        if not Caja.objects.filter(usuario=request.user, estado="abierta").exists():
            messages.error(request, "Debes abrir caja antes de vender (F6)")
            return redirect("ventas:caja")
        lineas = request.session.get("pos_lineas", [])
        q = request.GET.get("q", "").strip()
        productos = None

        # Modal de cliente (F10): CI/RIF exacto anexa solo
        cliente_q = request.GET.get("cliente_q", "").strip()
        modal_cliente = None
        if cliente_q:
            modal_cliente = {"q": cliente_q, "no_registrado": False, "candidatos": None}
            if re.fullmatch(r"(V|J|G)?\d{6,9}", cliente_q.upper()):
                exacto = Cliente.objects.filter(ci_nit__iexact=cliente_q).first()
                if exacto:
                    request.session["pos_cliente"] = str(exacto.pk)
                    messages.success(request, f"Cliente: {exacto.full_name}")
                    return redirect("ventas:pago")
                modal_cliente["no_registrado"] = True
            else:
                modal_cliente["candidatos"] = Cliente.objects.filter(
                    Q(nombres__icontains=cliente_q)
                    | Q(apellidos__icontains=cliente_q)
                    | Q(ci_nit__icontains=cliente_q)
                )[:8]

        # Clic en fila de resultados: agrega 1 o abre modal si es pesable
        agregar_id = request.GET.get("agregar")
        if agregar_id:
            producto = Producto.objects.filter(activo=True, pk=agregar_id).first()
            if producto:
                if producto.es_pesable:
                    total = sum((Decimal(l["subtotal"]) for l in lineas), Decimal("0.00")).quantize(Decimal("0.01"))
                    return render(request, "ventas/pos.html", {
                        "lineas": lineas, "productos": None, "q": "",
                        "total": total, **ctx_iva(lineas, total), "modal_producto": producto,
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
                total = sum((Decimal(l["subtotal"]) for l in lineas), Decimal("0.00")).quantize(Decimal("0.01"))
                return render(request, "ventas/pos.html", {
                    "lineas": lineas,
                    "productos": None,
                    "q": "",
                    "total": total, **ctx_iva(lineas, total),
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

        total = sum((Decimal(l["subtotal"]) for l in lineas), Decimal("0.00")).quantize(Decimal("0.01"))
        return render(request, "ventas/pos.html", {
            "lineas": lineas,
            "productos": productos,
            "q": q,
            "total": total, **ctx_iva(lineas, total),
            "modal_cliente": modal_cliente,
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
            request.session["pos_cliente"] = None

        elif accion == "cliente_pos":
            request.session["pos_cliente"] = request.POST.get("cliente") or None
            return redirect("ventas:pago")

        elif accion == "pagar":
            if not lineas:
                messages.info(request, "El ticket está vacío")
                return redirect("ventas:pos")
            if request.session.get("pos_cliente"):
                return redirect("ventas:pago")
            total = sum((Decimal(l["subtotal"]) for l in lineas), Decimal("0.00")).quantize(Decimal("0.01"))
            return render(request, "ventas/pos.html", {
                "lineas": lineas,
                "productos": None,
                "q": "",
                "total": total, **ctx_iva(lineas, total),
                "modal_cliente": {"q": "", "no_registrado": False, "candidatos": None},
                "title": "Nueva venta (POS)",
            })

        return redirect("ventas:pos")


class PagoView(LoginRequiredMixin, View):
    """Cobro: pagos parciales, vuelto, resto a crédito. La venta se crea al confirmar."""

    def _totales(self, request):
        lineas = request.session.get("pos_lineas", [])
        pagos = request.session.get("pos_pagos", [])
        total = sum((Decimal(l["subtotal"]) for l in lineas), Decimal("0.00")).quantize(Decimal("0.01"))
        pagado = sum((Decimal(p["monto"]) for p in pagos), Decimal("0.00")).quantize(Decimal("0.01"))
        return lineas, pagos, total, pagado

    def get(self, request):
        lineas, pagos, total, pagado = self._totales(request)
        if not lineas:
            return redirect("ventas:pos")
        if not Caja.objects.filter(usuario=request.user, estado="abierta").exists():
            messages.error(request, "Debes abrir caja antes de cobrar")
            return redirect("ventas:caja")
        cliente_id = request.session.get("pos_cliente")
        cliente = Cliente.objects.filter(pk=cliente_id).first() if cliente_id else None
        q_cliente = request.GET.get("q_cliente", "").strip()
        resultados_clientes = None
        if q_cliente:
            # CI/RIF exacto: selecciona sin mouse (como el escáner de productos)
            if re.fullmatch(r"(V|J|G)?\d{6,9}", q_cliente.upper()):
                exacto = Cliente.objects.filter(ci_nit__iexact=q_cliente).first()
                if exacto:
                    request.session["pos_cliente"] = str(exacto.pk)
                    messages.success(request, f"Cliente: {exacto.full_name}")
                    return redirect("ventas:pago")
            resultados_clientes = Cliente.objects.filter(
                Q(ci_nit__icontains=q_cliente)
                | Q(nombres__icontains=q_cliente)
                | Q(apellidos__icontains=q_cliente)
            )[:8]
        etiquetas = dict(Pago.METODOS)
        pagos_vista = [dict(p, metodo_label=etiquetas.get(p["metodo"], p["metodo"])) for p in pagos]
        return render(request, "ventas/pago.html", {
            "lineas": lineas, "pagos": pagos_vista,
            "total": total, **ctx_iva(lineas, total), "pagado": pagado,
            "falta": max(total - pagado, Decimal("0")),
            "cambio": max(pagado - total, Decimal("0")),
            "cliente": cliente,
            "q_cliente": q_cliente,
            "resultados_clientes": resultados_clientes,
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

                gravado = monto_gravado(lineas)
                base, iva = desglose_iva(total, gravado)
                venta = Venta.objects.create(
                    cliente=cliente, usuario=request.user,
                    subtotal=total, descuento=0, total=total,
                    base_imponible=base, monto_iva=iva,
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
        if not self.request.user.es_admin:
            qs = qs.filter(usuario=self.request.user)
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
        items = 0
        for d in self.object.detalles.select_related("producto"):
            items += 1 if d.producto.es_pesable else int(d.cantidad)
        ctx["total_items"] = items
        from core.models import ConfigNegocio
        ctx["config"] = ConfigNegocio.get()
        return ctx
