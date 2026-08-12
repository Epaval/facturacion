from django import forms
from .models import Producto


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ["nombre", "categoria", "codigo_barras", "precio_compra",
                  "precio_venta", "stock", "stock_minimo", "unidad", "activo", "grava_iva"]
