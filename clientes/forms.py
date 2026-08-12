import re

from django import forms
from .models import Cliente


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ["nombres", "apellidos", "ci_nit", "telefono", "direccion"]
        labels = {"ci_nit": "CI / RIF"}
        widgets = {
            "direccion": forms.Textarea(attrs={
                "rows": 2, "placeholder": "Calle, casa, sector, ciudad",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["nombres"].required = True
        self.fields["nombres"].widget.attrs.update({"placeholder": "Ej: María", "autofocus": True})
        self.fields["apellidos"].widget.attrs.update({"placeholder": "Ej: Pérez"})
        self.fields["ci_nit"].widget.attrs.update({"placeholder": "12345678 o V12345678"})
        self.fields["telefono"].widget.attrs.update({"placeholder": "Ej: 0414 5551234"})

    def clean_ci_nit(self):
        valor = (self.cleaned_data.get("ci_nit") or "").strip().upper()
        if valor and not re.fullmatch(r"(V|J|G)?\d{6,9}", valor):
            raise forms.ValidationError("Formato válido: 12345678 o V12345678 (V/J/G)")
        return valor
