from decimal import Decimal
from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import DetailView, ListView

from .models import DetalleVenta, NotaCredito, NotaCreditoDetalle, Venta, Caja


class NotaCreditoListView(LoginRequiredMixin, ListView):
    """Listado de todas las notas de crédito."""
    template_name = "ventas/notas_credito_list.html"
    context_object_name = "notas"
    paginate_by = 20

    def get_queryset(self):
        return NotaCredito.objects.select_related('factura', 'creado_por', 'autorizado_por').all()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Notas de crédito"
        return ctx


class NotaCreditoDetailView(LoginRequiredMixin, DetailView):
    """Detalle de una nota de crédito."""
    model = NotaCredito
    template_name = "ventas/notas_credito_detail.html"
    context_object_name = "nota"


class NotaCreditoCreateView(LoginRequiredMixin, View):
    """Crear nota de crédito: busca factura, valida productos y cantidades."""

    def get(self, request):
        q = request.GET.get("q", "").strip()
        factura = None
        productos_factura = []
        
        if q:
            # Buscar factura por número
            try:
                numero = int(q)
                factura = Venta.objects.filter(numero=numero, estado="completada").first()
            except ValueError:
                pass
            
            if factura:
                # Obtener productos de la factura con cantidad ya devuelta
                detalles = factura.detalles.select_related('producto').all()
                for d in detalles:
                    # Calcular cantidad ya devuelta
                    devuelto = NotaCreditoDetalle.objects.filter(
                        detalle_venta=d
                    ).aggregate(total=Sum('cantidad_devuelta'))['total'] or Decimal('0')
                    
                    remanente = d.cantidad - devuelto
                    
                    if remanente > 0:
                        productos_factura.append({
                            'detalle': d,
                            'producto': d.producto,
                            'cantidad_original': d.cantidad,
                            'devuelto': devuelto,
                            'remanente': remanente,
                            'precio': d.precio_unitario,
                        })
        
        ctx = {
            "title": "Nueva nota de crédito",
            "q": q,
            "factura": factura,
            "productos": productos_factura,
        }
        return render(request, "ventas/notas_credito_create.html", ctx)

    def post(self, request):
        factura_id = request.POST.get("factura_id")
        motivo = request.POST.get("motivo", "").strip()
        
        if not factura_id or not motivo:
            messages.error(request, "Debes seleccionar una factura y especificar el motivo")
            return redirect("ventas:notas_credito_create")
        
        factura = get_object_or_404(Venta, pk=factura_id, estado="completada")
        
        # Verificar que el usuario tiene caja abierta
        caja = Caja.objects.filter(usuario=request.user, estado="abierta").first()
        if not caja:
            messages.error(request, "Debes abrir caja antes de crear notas de crédito")
            return redirect("ventas:caja")
        
        # Procesar productos seleccionados
        detalles_data = []
        total = Decimal("0.00")
        
        for key, value in request.POST.items():
            if key.startswith("producto_"):
                detalle_id = int(key.split("_")[1])
                try:
                    cantidad = Decimal(value.replace(",", ".") or "0")
                except:
                    cantidad = Decimal("0")
                
                if cantidad > 0:
                    detalle = DetalleVenta.objects.get(pk=detalle_id, venta=factura)
                    
                    # Validar cantidad no exceda remanente
                    devuelto = NotaCreditoDetalle.objects.filter(
                        detalle_venta=detalle
                    ).aggregate(total=Sum('cantidad_devuelta'))['total'] or Decimal('0')
                    
                    remanente = detalle.cantidad - devuelto
                    
                    if cantidad > remanente:
                        messages.error(request, f"La cantidad de {detalle.producto.nombre} excede el remanente ({remanente})")
                        return redirect(f"{request.path}?q={factura.numero}")
                    
                    monto = (cantidad * detalle.precio_unitario).quantize(Decimal("0.01"))
                    total += monto
                    
                    detalles_data.append({
                        'detalle': detalle,
                        'cantidad': cantidad,
                        'monto': monto,
                    })
        
        if not detalles_data:
            messages.error(request, "Debes seleccionar al menos un producto a devolver")
            return redirect(f"{request.path}?q={factura.numero}")
        
        # Validar que el total no exceda el de la factura
        total_factura = factura.total
        notas_existentes = NotaCredito.objects.filter(factura=factura).aggregate(
            total=Sum('total')
        )['total'] or Decimal('0')
        
        if notas_existentes + total > total_factura:
            messages.error(request, f"El monto excede el total de la factura (ya hay {notas_existentes} en notas)")
            return redirect(f"{request.path}?q={factura.numero}")
        
        # Guardar en sesión temporal (esperando autorización)
        request.session['nc_pendiente'] = {
            'factura_id': factura.id,
            'motivo': motivo,
            'detalles': [
                {'detalle_id': d['detalle'].id, 'cantidad': str(d['cantidad']), 'monto': str(d['monto'])}
                for d in detalles_data
            ],
            'total': str(total),
        }
        
        # Redirigir al detalle para confirmar
        return render(request, "ventas/notas_credito_confirmar.html", {
            "factura": factura,
            "motivo": motivo,
            "detalles": detalles_data,
            "total": total,
        })


class NotaCreditoConfirmarView(LoginRequiredMixin, View):
    """Confirmar y crear la nota de crédito (requiere autorización si no es admin)."""
    
    def post(self, request):
        nc_data = request.session.get('nc_pendiente')
        if not nc_data:
            messages.error(request, "No hay nota de crédito pendiente")
            return redirect("ventas:notas_credito_create")
        
        # Obtener usuario y contraseña del form
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        
        if request.user.es_admin and not username:
            # Admin se auto-autoriza con su propia sesión
            user = request.user
        else:
            user = authenticate(request, username=username, password=password)
            if not user:
                return JsonResponse({"ok": False, "error": "Usuario o contraseña incorrectos"})
            if not user.es_admin:
                return JsonResponse({"ok": False, "error": "El usuario no es administrador"})
        
        # Crear la nota de crédito
        factura = Venta.objects.get(pk=nc_data['factura_id'])
        caja = Caja.objects.filter(usuario=request.user, estado="abierta").first()
        
        if not caja:
            return JsonResponse({"ok": False, "error": "No tienes caja abierta"})
        
        nota = NotaCredito.objects.create(
            factura=factura,
            caja_procesamiento=caja,
            creado_por=request.user,
            autorizado_por=user,
            motivo=nc_data['motivo'],
            total=Decimal(nc_data['total']),
        )
        
        # Crear detalles
        for d in nc_data['detalles']:
            detalle = DetalleVenta.objects.get(pk=d['detalle_id'])
            NotaCreditoDetalle.objects.create(
                nota_credito=nota,
                detalle_venta=detalle,
                cantidad_devuelta=Decimal(d['cantidad']),
                monto=Decimal(d['monto']),
            )
        
        # Limpiar sesión
        del request.session['nc_pendiente']
        
        messages.success(request, f"Nota de crédito #{nota.id} creada por Bs {nota.total}")
        return JsonResponse({"ok": True, "redirect": f"/ventas/notas-credito/{nota.id}/"})
