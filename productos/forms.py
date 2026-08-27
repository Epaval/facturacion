from productos.models import Categoria
from django import forms
from .models import Producto


class ProductoForm(forms.ModelForm):
    nueva_categoria = forms.CharField(
        label="O escribe una categoría nueva", required=False, max_length=60,
        help_text="Si no existe se crea al guardar (ej: Viveres, Charcutería, Ropa)")
    categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.all(), required=False,
        label="Categoría", empty_label="- Selecciona una opción -")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # "O nueva categoría" justo después del select de Categoría
        self.order_fields(["nombre", "categoria", "nueva_categoria"])

    def clean(self):
        cleaned = super().clean()
        nueva = (cleaned.get("nueva_categoria") or "").strip()
        if nueva:
            cleaned["categoria"], _ = Categoria.objects.get_or_create(nombre=nueva)
        elif not cleaned.get("categoria"):
            self.add_error("categoria", "Selecciona una categoría o escribe una nueva.")
        return cleaned

    class Meta:
        model = Producto
        fields = ["nombre", "categoria", "codigo_barras", "precio_compra",
                  "precio_venta", "stock", "stock_minimo", "unidad", "activo", "grava_iva", "por_peso"]
