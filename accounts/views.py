from accounts.models import Empleado
from core.mixins import AdminRequiredMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse
from django.views.generic import CreateView, ListView, UpdateView
from django.shortcuts import render

# Create your views here.


class UsuarioListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = Empleado
    template_name = "accounts/usuario_list.html"
    context_object_name = "usuarios"

    def get_queryset(self):
        return Empleado.objects.order_by("username")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Usuarios del sistema"
        return ctx


class UsuarioCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Empleado
    template_name = "accounts/usuario_form.html"
    fields = ["username", "nombres", "apellidos", "rol", "is_active"]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Nuevo usuario"
        ctx["creando"] = True
        return ctx

    def form_valid(self, form):
        password = self.request.POST.get("password_nueva", "").strip()
        if len(password) < 6:
            messages.error(self.request, "Contraseña obligatoria de al menos 6 caracteres")
            return self.form_invalid(form)
        response = super().form_valid(form)
        self.object.set_password(password)
        self.object.save()
        messages.success(self.request, f"Usuario {self.object.username} creado")
        return response

    def get_success_url(self):
        try:
            return reverse("accounts:usuarios")
        except Exception:
            return reverse("usuarios")


class UsuarioUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Empleado
    template_name = "accounts/usuario_form.html"
    fields = ["nombres", "apellidos", "rol", "is_active"]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = f"Editar usuario: {self.object.username}"
        ctx["creando"] = False
        return ctx

    def form_valid(self, form):
        # No puedes desactivarte a ti mismo
        if self.object.pk == self.request.user.pk and not form.cleaned_data.get("is_active"):
            form.cleaned_data["is_active"] = True
            messages.error(self.request, "No puedes desactivar tu propio usuario")
        response = super().form_valid(form)
        nueva = self.request.POST.get("password_nueva", "").strip()
        if nueva:
            if len(nueva) < 6:
                messages.error(self.request, "La contraseña debe tener al menos 6 caracteres")
            else:
                self.object.set_password(nueva)
                self.object.save()
                messages.success(self.request, "Contraseña actualizada")
        else:
            messages.success(self.request, "Usuario actualizado")
        return response

    def get_success_url(self):
        try:
            return reverse("accounts:usuarios")
        except Exception:
            return reverse("usuarios")
