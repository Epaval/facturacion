from django.shortcuts import render, redirect
from django.contrib import messages
from accounts.models import Empleado


def recuperar_clave(request):
    """Restablece la contraseña usando solo el nombre de usuario (entorno local)."""
    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        p1 = request.POST.get("password1") or ""
        p2 = request.POST.get("password2") or ""
        user = Empleado.objects.filter(username__iexact=username, is_active=True).first()
        if not user:
            messages.error(request, "El usuario no existe o está inactivo.")
        elif len(p1) < 6:
            messages.error(request, "La contraseña debe tener al menos 6 caracteres.")
        elif p1 != p2:
            messages.error(request, "Las contraseñas no coinciden.")
        else:
            user.set_password(p1)
            user.save()
            messages.success(request, f"Contraseña de {user.username} actualizada. Ya puedes entrar.")
            return redirect("accounts:login")
    return render(request, "registration/recuperar.html")
