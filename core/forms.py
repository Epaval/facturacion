from django import forms
from .models import ConfigNegocio


class ConfigNegocioForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["tasa_dolar"].required = False
    class Meta:
        model = ConfigNegocio
        fields = ["nombre", "rif", "nit", "direccion", "telefono",
                  "serial_impresora_fiscal", "logo", "notas_factura", "tasa_dolar"]
        widgets = {
            "direccion": forms.Textarea(attrs={"rows": 2}),
            "notas_factura": forms.Textarea(attrs={"rows": 2}),
        }


class LicenciaForm(forms.Form):
    clave = forms.CharField(max_length=30, label="Clave de licencia")
