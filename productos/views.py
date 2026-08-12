from django.contrib.auth.mixins import LoginRequiredMixin

from core.mixins import AdminRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

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
