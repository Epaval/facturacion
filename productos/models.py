from django.db import models


class Categoria(models.Model):
    nombre = models.CharField(max_length=60, unique=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    UNIDADES = [
        ("unidad", "Unidad"), ("kg", "Kilogramo"), ("g", "Gramo"),
        ("lb", "Libra"), ("l", "Litro"), ("ml", "Mililitro"),
        ("docena", "Docena"), ("paquete", "Paquete"),
    ]

    nombre = models.CharField(max_length=120)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name="productos")
    codigo_barras = models.CharField(max_length=40, blank=True, null=True, unique=True)
    precio_compra = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    precio_venta = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    stock = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    stock_minimo = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    unidad = models.CharField(max_length=10, choices=UNIDADES, default="unidad")
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nombre"]

    @property
    def es_pesable(self):
        return self.unidad in ("kg", "g", "lb")

    @property
    def stock_bajo(self):
        return self.stock <= self.stock_minimo

    def __str__(self):
        return self.nombre
