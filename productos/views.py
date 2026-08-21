import csv
import io
import logging
from decimal import Decimal, InvalidOperation
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView, TemplateView

from core.mixins import AdminRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q

from .forms import ProductoForm
from .models import Categoria, Producto

# Configurar logger
logger = logging.getLogger(__name__)


DEBUG_LOG = '/tmp/import_debug.log'

def debug_log(msg):
    """Escribe mensajes de depuración a un archivo"""
    try:
        with open(DEBUG_LOG, 'a') as f:
            from datetime import datetime
            f.write(f"{datetime.now().strftime('%H:%M:%S')} - {msg}\n")
            f.flush()  # Forzar escritura inmediata
    except Exception as e:
        # Si falla, intentar escribir en otro lugar
        try:
            with open('/tmp/debug_fallback.log', 'a') as f:
                f.write(f"ERROR en debug_log: {e}\n")
        except:
            pass

class ProductoListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = Producto
    template_name = "productos/producto_list.html"
    context_object_name = "object_list"
    paginate_by = 15

    def get_queryset(self):
        qs = super().get_queryset().select_related("categoria")
        q = self.request.GET.get("q", "").strip()
        cat = self.request.GET.get("categoria", "").strip()
        if q:
            qs = qs.filter(Q(nombre__icontains=q) | Q(codigo_barras__icontains=q))
        if cat:
            qs = qs.filter(categoria_id=cat)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        ctx["categorias"] = Categoria.objects.all()
        ctx["categoria_sel"] = self.request.GET.get("categoria", "")
        ctx["title"] = "Productos"
        return ctx


class ProductoCreateView(LoginRequiredMixin, AdminRequiredMixin, SuccessMessageMixin, CreateView):
    model = Producto
    form_class = ProductoForm
    template_name = "productos/producto_form.html"
    success_url = reverse_lazy("productos:list")
    success_message = "Producto registrado correctamente"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Registrar producto"
        return ctx


class ProductoUpdateView(LoginRequiredMixin, AdminRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Producto
    form_class = ProductoForm
    template_name = "productos/producto_form.html"
    success_url = reverse_lazy("productos:list")
    success_message = "Producto actualizado"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = f"Editar producto: {self.object.nombre}"
        ctx["volver"] = self.request.GET.get("volver", "")
        return ctx

    def get_success_url(self):
        volver = self.request.POST.get("volver") or self.request.GET.get("volver") or ""
        if volver.startswith("/productos/"):
            return volver
        return str(reverse_lazy("productos:list"))


class ProductoImportView(AdminRequiredMixin, TemplateView):
    """Importa productos masivamente desde CSV."""
    template_name = "productos/importar.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Importar productos"
        return ctx

    def post(self, request, *args, **kwargs):
        debug_log("=" * 60)
        debug_log("INICIANDO POST DE IMPORTACIÓN")
        debug_log("=" * 60)
        
        debug_log(f"FILES: {request.FILES}")
        debug_log(f"POST: {request.POST}")
        
        archivo = request.FILES.get("archivo")
        if not archivo:
            debug_log("ERROR: No se recibió archivo")
            messages.error(request, "Selecciona un archivo CSV")
            return self.render_to_response(self.get_context_data())

        debug_log(f"Archivo recibido: {archivo.name}")
        debug_log(f"Tamaño: {archivo.size} bytes")
        debug_log(f"Tipo: {archivo.content_type}")
        
        if not archivo.name.endswith('.csv'):
            debug_log(f"EXTENSIÓN INCORRECTA: {archivo.name}")
            messages.error(request, "El archivo debe tener extensión .csv")
            return self.render_to_response(self.get_context_data())

        try:
            contenido = archivo.read()
            debug_log(f"Contenido leído: {len(contenido)} bytes")
            
            try:
                texto = contenido.decode('utf-8-sig')
                debug_log("DECODIFICACIÓN OK")
                debug_log(f"Primeros 300 caracteres:")
                debug_log(texto[:300])

                # ============================================
                # LIMPIAR COMILLAS DOBLES DEL CSV
                # ============================================
                # Dividir en líneas y limpiar cada una
                lineas_originales = texto.splitlines()
                debug_log(f"Número de líneas originales: {len(lineas_originales)}")

                lineas_limpias = []
                for linea in lineas_originales:
                    linea = linea.strip()
                    # Si la línea tiene comillas al inicio y final, quitarlas
                    if linea.startswith('"') and linea.endswith('"'):
                        linea = linea[1:-1]  # Quita la primera y última comilla
                    lineas_limpias.append(linea)

                # Unir las líneas limpias
                texto_limpio = '\n'.join(lineas_limpias)
                debug_log(f"Número de líneas después de limpiar: {len(lineas_limpias)}")
                if lineas_limpias:
                    debug_log(f"Cabecera limpia: {lineas_limpias[0]}")
                    if len(lineas_limpias) > 1:
                        debug_log(f"Primer producto limpio: {lineas_limpias[1]}")
                # ============================================

                # Usar texto_limpio en lugar de texto
                csv_data = io.StringIO(texto_limpio)
                reader = csv.DictReader(csv_data)
                
                debug_log(f"Columnas encontradas: {reader.fieldnames}")
                
                creados = 0
                actualizados = 0
                errores = 0
                
                for row_num, row in enumerate(reader, start=2):
                    try:
                        nombre = row.get('nombre', '').strip()
                        if not nombre:
                            debug_log(f"Fila {row_num}: Nombre vacío")
                            errores += 1
                            continue
                        
                        # Obtener categoría
                        categoria_nombre = row.get('categoria', 'General').strip() or 'General'
                        categoria, _ = Categoria.objects.get_or_create(nombre=categoria_nombre)
                        
                        # Convertir a Decimal
                        def to_decimal(valor, default=0):
                            if not valor or str(valor).strip() == '':
                                return Decimal(str(default))
                            try:
                                valor_str = str(valor).replace(',', '.').strip()
                                return Decimal(valor_str)
                            except:
                                return Decimal(str(default))
                        
                        codigo = row.get('codigo_barras', '').strip()
                        codigo = codigo if codigo else None
                        
                        grava_iva = row.get('grava_iva', '').strip().lower() in ('si', 'sí', '1', 'true')
                        
                        producto, creado = Producto.objects.update_or_create(
                            codigo_barras=codigo,
                            defaults={
                                'nombre': nombre,
                                'categoria': categoria,
                                'unidad': row.get('unidad', 'unidad').strip() or 'unidad',
                                'precio_venta': to_decimal(row.get('precio_venta', 0)),
                                'precio_compra': to_decimal(row.get('precio_compra', 0)),
                                'stock': to_decimal(row.get('stock', 0)),
                                'stock_minimo': to_decimal(row.get('stock_minimo', 0)),
                                'grava_iva': grava_iva,
                            }
                        )
                        
                        if creado:
                            creados += 1
                        else:
                            actualizados += 1
                            
                        if row_num % 10 == 0:
                            debug_log(f"Procesados {row_num-1} registros...")
                            
                    except Exception as e:
                        errores += 1
                        debug_log(f"ERROR en línea {row_num}: {e}")
                        debug_log(f"Row: {row}")
                        continue
                
                debug_log("=" * 60)
                debug_log(f"RESUMEN: {creados} creados, {actualizados} actualizados, {errores} errores")
                debug_log("=" * 60)
                
                mensaje = f"Importación completada: {creados} creados, {actualizados} actualizados"
                if errores > 0:
                    mensaje += f", {errores} con error"
                    messages.warning(request, mensaje)
                else:
                    messages.success(request, mensaje)
                
            except UnicodeDecodeError as e:
                debug_log(f"ERROR DE DECODIFICACIÓN: {e}")
                messages.error(request, "El archivo debe estar en formato UTF-8")
                return self.render_to_response(self.get_context_data())
            
        except Exception as e:
            debug_log(f"ERROR GENERAL: {e}")
            import traceback
            debug_log(traceback.format_exc())
            messages.error(request, f"Error al procesar el archivo: {str(e)}")
        
        return redirect("productos:list")

from django.contrib.auth.decorators import login_required as _login_required
from django.http import JsonResponse as _JsonResponse
from django.db.models import Q as _Q

@_login_required
def buscar_global(request):
    """Buscador global: código exacto o descripción (JSON)."""
    q = (request.GET.get("q") or "").strip()
    if not q:
        return _JsonResponse({"productos": []})
    qs = Producto.objects.filter(activo=True).filter(
        _Q(nombre__icontains=q) | _Q(codigo_barras__icontains=q)
    )[:12]
    data = []
    for p in qs:
        data.append({
            "id": p.id,
            "nombre": p.nombre,
            "codigo": p.codigo_barras or "",
            "precio": str(getattr(p, "precio_venta", "")),
            "stock": str(p.stock),
            "unidad": p.unidad or "",
            "por_peso": bool(getattr(p, "por_peso", False)),
            "categoria": str(getattr(p, "categoria", "") or ""),
        })
    return _JsonResponse({"productos": data})
