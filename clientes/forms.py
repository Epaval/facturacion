from django import forms
from .models import Cliente


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ["nombres", "apellidos", "ci_nit", "telefono", "email",
                  "direccion", "credito_habilitado", "limite_credito", "notas"]
