import csv
import io
from decimal import Decimal, InvalidOperation
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages  # ← IMPORTANTE: Agregar esta importación
from django.shortcuts import redirect  # ← IMPORTANTE: Agregar esta importación
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView, TemplateView

from core.mixins import AdminRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q

from .forms import ProductoForm
from .models import Categoria, Producto


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
        return ctx


class ProductoImportView(AdminRequiredMixin, TemplateView):
    """Importa productos masivamente desde CSV (exportable desde Excel)."""
    template_name = "productos/importar.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Importar productos"
        return ctx

    def post(self, request, *args, **kwargs):
        archivo = request.FILES.get("archivo")
        if not archivo:
            messages.error(request, "Selecciona un archivo CSV")
            return self.render_to_response(self.get_context_data())

        # Verificar extensión del archivo
        if not archivo.name.endswith('.csv'):
            messages.error(request, "El archivo debe tener extensión .csv")
            return self.render_to_response(self.get_context_data())

        try:
            data = archivo.read().decode("utf-8-sig")
        except UnicodeDecodeError:
            messages.error(request, "El archivo debe estar en formato CSV (UTF-8)")
            return self.render_to_response(self.get_context_data())

        creados = actualizados = errores = 0
        lineas_procesadas = 0
        
        try:
            reader = csv.DictReader(io.StringIO(data))
            
            # Verificar que el CSV tiene las columnas necesarias
            expected_headers = ['nombre', 'codigo_barras', 'categoria', 'unidad', 
                              'precio_venta', 'precio_compra', 'stock', 'stock_minimo', 'grava_iva']
            
            if reader.fieldnames:
                # Mostrar columnas encontradas para depuración
                print(f"Columnas encontradas: {reader.fieldnames}")
            
            for i, row in enumerate(reader, start=2):
                lineas_procesadas += 1
                try:
                    nombre = (row.get("nombre") or "").strip()
                    codigo = (row.get("codigo_barras") or "").strip()
                    
                    if not nombre:
                        errores += 1
                        continue
                    
                    # Obtener o crear categoría
                    categoria_nombre = (row.get("categoria") or "General").strip() or "General"
                    cat, _ = Categoria.objects.get_or_create(nombre=categoria_nombre)
                    
                    # Función para convertir a Decimal de forma segura
                    def dec(v, d="0"):
                        if not v or str(v).strip() == "":
                            return Decimal(d)
                        try:
                            # Reemplazar coma por punto para decimales
                            valor = str(v).replace(",", ".").strip()
                            return Decimal(valor)
                        except (InvalidOperation, ValueError):
                            return Decimal(d)
                    
                    # Determinar si grava IVA
                    grava_iva_val = (row.get("grava_iva") or "").strip().lower()
                    grava_iva = grava_iva_val in ("si", "sí", "1", "true", "yes", "y")
                    
                    # Crear o actualizar producto
                    prod, creado = Producto.objects.update_or_create(
                        codigo_barras=codigo if codigo else None,
                        defaults={
                            'nombre': nombre,
                            'categoria': cat,
                            'unidad': (row.get("unidad") or "unidad").strip(),
                            'precio_venta': dec(row.get("precio_venta"), "0"),
                            'precio_compra': dec(row.get("precio_compra"), "0"),
                            'stock': dec(row.get("stock"), "0"),
                            'stock_minimo': dec(row.get("stock_minimo"), "0"),
                            'grava_iva': grava_iva,
                        }
                    )
                    
                    if creado:
                        creados += 1
                    else:
                        actualizados += 1
                        
                except Exception as e:
                    errores += 1
                    # Log del error para depuración
                    print(f"Error en línea {i}: {e}")
                    continue

        except csv.Error as e:
            messages.error(request, f"Error al leer el archivo CSV: {e}")
            return self.render_to_response(self.get_context_data())
        
        # Mensaje de éxito con detalles
        mensaje = f"Importación completada: {creados} creados, {actualizados} actualizados"
        if errores > 0:
            mensaje += f", {errores} con error"
            messages.warning(request, mensaje)
        else:
            messages.success(request, mensaje)
            
        return redirect("productos:list")